"""OCR adapter built on Apple's Vision framework, the text recognition macOS ships.

It reads scanned PDFs and photos on a Mac without installing or downloading a
model: the recognizer is part of the operating system, the same one that lets
Photos select text in a picture. Each PDF page is rendered to a bitmap with
pypdfium2 and handed to Vision; an image file goes to Vision as it is.

The cost is structure. Vision returns lines of text and where they sit on the
page, so this adapter rebuilds paragraphs from the gaps between lines and
nothing more: no heading levels, no tables, no reading order across columns
beyond what Vision reports. It runs only on macOS.
"""
import io
import re
import statistics
import sys
from dataclasses import dataclass
from pathlib import Path

from .base import Engine, EngineError
from ..models import ConversionResult, ImageMode

IMAGE_SUFFIXES = frozenset({".png", ".jpg", ".jpeg", ".webp"})

# Recognition languages in order of preference. Vision weighs the first most,
# and Traditional Chinese leads because it is this project's first interface
# language. Any the running macOS does not offer are left out.
LANGUAGES = ("zh-Hant", "zh-Hans", "en-US")

# PDF pages are rendered at 300 dpi; PDF user space is 72 units per inch.
RENDER_SCALE = 300 / 72

# A vertical gap between two lines wider than this share of the typical line
# height starts a new paragraph.
PARAGRAPH_GAP = 0.75

QUALITY_WARNING = (
    "apple-vision recognized the text with macOS's built-in OCR: it rebuilds paragraphs only, "
    "with no heading levels or tables, and recognition can be wrong. Check the output before relying on it."
)

NO_TEXT_WARNING = "No text was recognized. The pages may be blank, pictures without text, or too faint to read."

_CJK = re.compile(r"[　-〿぀-ヿ㐀-䶿一-鿿가-힯豈-﫿＀-￯]")


@dataclass(frozen=True)
class Line:
    """One recognized line, its box in page fractions measured from the top left."""

    text: str
    top: float
    height: float

    @property
    def bottom(self) -> float:
        return self.top + self.height


def _joined(left: str, right: str) -> str:
    """Join two lines of one paragraph: no space between Chinese, Japanese or Korean."""
    if _CJK.match(left[-1:]) or _CJK.match(right[:1]):
        return left + right
    return left + " " + right


def paragraphs(lines: list[Line]) -> list[str]:
    """Group lines, in the order Vision reported them, into paragraphs.

    A paragraph ends where the gap to the next line is wider than usual, or where
    the next line starts above the previous one: Vision has moved to another
    column or block.
    """
    lines = [line for line in lines if line.text.strip()]
    if not lines:
        return []
    typical = statistics.median(line.height for line in lines)
    result = [lines[0].text.strip()]
    for previous, line in zip(lines, lines[1:]):
        gap = line.top - previous.bottom
        if gap > typical * PARAGRAPH_GAP or line.top < previous.top:
            result.append(line.text.strip())
        else:
            result[-1] = _joined(result[-1], line.text.strip())
    return result


def _vision():
    if sys.platform != "darwin":
        raise EngineError("apple-vision runs only on macOS: it uses the Vision framework built into the system")
    try:
        import objc
        import Vision
    except Exception as e:
        raise EngineError(f"Apple Vision is unavailable: {e}. Install it with: pip install pyobjc-framework-Vision") from e
    return objc, Vision


def recognize(image, objc, Vision) -> list[Line]:
    """Run Vision's accurate text recognizer on one PIL image."""
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    with objc.autorelease_pool():
        request = Vision.VNRecognizeTextRequest.alloc().init()
        request.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)
        request.setUsesLanguageCorrection_(True)
        supported, _ = request.supportedRecognitionLanguagesAndReturnError_(None)
        languages = [language for language in LANGUAGES if language in set(supported or ())]
        if languages:
            request.setRecognitionLanguages_(languages)
        handler = Vision.VNImageRequestHandler.alloc().initWithData_options_(buffer.getvalue(), None)
        outcome = handler.performRequests_error_([request], None)
        ok, error = outcome if isinstance(outcome, tuple) else (bool(outcome), None)
        if not ok or error is not None:
            raise EngineError(f"Apple Vision could not read the image: {error}")
        lines = []
        for observation in request.results() or ():
            candidates = observation.topCandidates_(1)
            if not candidates:
                continue
            box = observation.boundingBox()
            # Vision measures from the bottom left; turn it round to read top down.
            top = 1.0 - (box.origin.y + box.size.height)
            lines.append(Line(str(candidates[0].string()), top, box.size.height))
        return lines


def page_images(path: Path):
    """Yield each page of a PDF, or the image itself, as an RGB PIL image."""
    from PIL import Image, ImageOps

    if path.suffix.lower() == ".pdf":
        import pypdfium2

        document = pypdfium2.PdfDocument(str(path))
        try:
            for index in range(len(document)):
                page = document[index]
                try:
                    yield page.render(scale=RENDER_SCALE).to_pil().convert("RGB")
                finally:
                    page.close()
        finally:
            document.close()
    else:
        with Image.open(path) as image:
            # A phone photo is often stored sideways with an orientation tag;
            # Vision reads the pixels as stored, so turn them upright first.
            yield ImageOps.exif_transpose(image).convert("RGB")


class AppleVisionOcrEngine(Engine):
    name = "apple-vision"

    def can_handle(self, path: Path) -> bool:
        suffix = path.suffix.lower()
        return suffix == ".pdf" or suffix in IMAGE_SUFFIXES

    def convert(self, path: Path, image_mode: ImageMode) -> ConversionResult:
        if not self.can_handle(path):
            raise EngineError(f"apple-vision only reads PDF and image input, not {path.suffix or 'unknown'}")
        objc, Vision = _vision()
        try:
            found = []
            for image in page_images(path):
                found.extend(paragraphs(recognize(image, objc, Vision)))
        except EngineError:
            raise
        except Exception as e:
            raise EngineError(f"apple-vision failed for {path}: {e}") from e

        text = "\n\n".join(found)
        result = ConversionResult(
            source=path,
            engine=self.name,
            markdown=text + "\n" if text else "",
            text=text + "\n" if text else "",
        )
        result.warnings.append(QUALITY_WARNING)
        if not found:
            result.warnings.append(NO_TEXT_WARNING)
        return result
