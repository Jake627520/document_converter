"""apple-vision adapter contracts with a stand-in Vision framework.

The real framework exists only on macOS; tests/test_apple_vision_macos.py runs
it there. These tests pin what the adapter does with what Vision returns, and
run everywhere.
"""
import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from PIL import Image

from document_converter.engines import apple_vision_engine
from document_converter.engines.apple_vision_engine import (
    LANGUAGES,
    NO_TEXT_WARNING,
    QUALITY_WARNING,
    AppleVisionOcrEngine,
    Line,
    paragraphs,
)
from document_converter.engines.base import EngineError
from document_converter.models import no_text_recovered_message


def on_platform(name):
    """Make only the adapter believe it runs on this platform.

    Patching sys.platform itself would mislead every library that loads native
    code during the test, pypdfium2 among them.
    """
    return patch.object(apple_vision_engine, "sys", SimpleNamespace(platform=name))


def observation(text, top, height=0.02):
    """A recognized line as Vision reports it: its box measured from the bottom left."""
    box = SimpleNamespace(
        origin=SimpleNamespace(x=0.1, y=1.0 - top - height),
        size=SimpleNamespace(width=0.5, height=height),
    )
    candidate = SimpleNamespace(string=lambda: text)
    return SimpleNamespace(boundingBox=lambda: box, topCandidates_=lambda n: [candidate])


class FakeVision:
    """Records each image handed to Vision and answers with prepared lines."""

    VNRequestTextRecognitionLevelAccurate = 0

    def __init__(self, pages, supported=("en-US", "zh-Hans", "zh-Hant", "fr-FR")):
        self.pages = list(pages)
        self.supported = list(supported)
        self.images = []
        self.languages = None
        vision = self

        class Request:
            def __init__(self):
                self._results = []

            def setRecognitionLevel_(self, level):
                vision.level = level

            def setUsesLanguageCorrection_(self, value):
                vision.correction = value

            def supportedRecognitionLanguagesAndReturnError_(self, error):
                return vision.supported, None

            def setRecognitionLanguages_(self, languages):
                vision.languages = list(languages)

            def results(self):
                return self._results

        class Handler:
            def __init__(self, data):
                self.data = data

            def performRequests_error_(self, requests, error):
                with Image.open(io.BytesIO(self.data)) as image:
                    vision.images.append(image.size)
                requests[0]._results = vision.pages.pop(0)
                return True, None

        self.VNRecognizeTextRequest = SimpleNamespace(alloc=lambda: SimpleNamespace(init=Request))
        self.VNImageRequestHandler = SimpleNamespace(
            alloc=lambda: SimpleNamespace(initWithData_options_=lambda data, options: Handler(data))
        )


class ParagraphTests(unittest.TestCase):
    def test_lines_close_together_form_one_paragraph(self):
        lines = [Line("The quick brown", 0.10, 0.02), Line("fox jumps.", 0.125, 0.02)]
        self.assertEqual(paragraphs(lines), ["The quick brown fox jumps."])

    def test_chinese_lines_join_without_a_space(self):
        lines = [Line("營收成長", 0.10, 0.02), Line("百分之十二", 0.125, 0.02)]
        self.assertEqual(paragraphs(lines), ["營收成長百分之十二"])

    def test_a_wide_gap_starts_a_new_paragraph(self):
        lines = [Line("First.", 0.10, 0.02), Line("Second.", 0.20, 0.02)]
        self.assertEqual(paragraphs(lines), ["First.", "Second."])

    def test_moving_back_up_the_page_starts_a_new_paragraph(self):
        # Vision has finished the left column and gone to the top of the right.
        lines = [Line("Left column end", 0.80, 0.02), Line("Right column top", 0.10, 0.02)]
        self.assertEqual(paragraphs(lines), ["Left column end", "Right column top"])

    def test_blank_lines_are_dropped(self):
        self.assertEqual(paragraphs([Line("  ", 0.1, 0.02)]), [])


class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def convert(self, path, vision):
        # The stand-ins are handed to the adapter directly. Swapping them into
        # sys.modules would drop whatever the conversion imports meanwhile -
        # pypdfium2 among them - and loading a native library twice is not safe.
        objc = SimpleNamespace(autorelease_pool=contextlib.nullcontext)
        with patch.object(apple_vision_engine, "_vision", return_value=(objc, vision)):
            return AppleVisionOcrEngine().convert(path, "none")

    def test_reads_an_image(self):
        source = self.tmp / "receipt.png"
        Image.new("RGB", (400, 200), "white").save(source)
        vision = FakeVision([[observation("Total", 0.10), observation("NT$ 120", 0.125), observation("謝謝光臨", 0.30)]])
        result = self.convert(source, vision)
        self.assertEqual(result.engine, "apple-vision")
        self.assertEqual(result.markdown, "Total NT$ 120\n\n謝謝光臨\n")
        self.assertEqual(result.text, result.markdown)
        self.assertIsNone(result.json_text)
        self.assertEqual(result.warnings, [QUALITY_WARNING])
        self.assertEqual(vision.images, [(400, 200)])
        self.assertEqual(vision.level, 0)
        self.assertTrue(vision.correction)

    def test_asks_for_the_languages_this_macos_offers_in_preference_order(self):
        source = self.tmp / "note.png"
        Image.new("RGB", (10, 10), "white").save(source)
        vision = FakeVision([[observation("x", 0.1)]], supported=("en-US", "zh-Hant"))
        self.convert(source, vision)
        self.assertEqual(vision.languages, [language for language in LANGUAGES if language in {"en-US", "zh-Hant"}])
        self.assertEqual(vision.languages[0], "zh-Hant")

    def test_turns_a_sideways_phone_photo_upright(self):
        source = self.tmp / "photo.jpg"
        exif = Image.Exif()
        exif[0x0112] = 6  # stored rotated: display turned 90 degrees
        Image.new("RGB", (300, 100), "white").save(source, exif=exif)
        vision = FakeVision([[observation("x", 0.1)]])
        self.convert(source, vision)
        self.assertEqual(vision.images, [(100, 300)])

    def test_reads_every_page_of_a_pdf_in_order(self):
        source = self.tmp / "scan.pdf"
        first = Image.new("RGB", (612, 792), "white")
        first.save(source, save_all=True, append_images=[Image.new("RGB", (612, 792), "white")])
        vision = FakeVision([[observation("Page one", 0.1)], [observation("第二頁", 0.1)]])
        result = self.convert(source, vision)
        self.assertEqual(result.markdown, "Page one\n\n第二頁\n")
        # 300 dpi: a 612 x 792 point page renders at about 2550 x 3300 pixels.
        self.assertEqual(len(vision.images), 2)
        for width, height in vision.images:
            self.assertAlmostEqual(width, 2550, delta=2)
            self.assertAlmostEqual(height, 3300, delta=2)

    def test_nothing_recognized_is_reported_not_returned_empty(self):
        source = self.tmp / "blank.png"
        Image.new("RGB", (10, 10), "white").save(source)
        result = self.convert(source, FakeVision([[]]))
        self.assertFalse(result.has_recovered_text())
        self.assertEqual(result.warnings, [QUALITY_WARNING, NO_TEXT_WARNING])
        message = no_text_recovered_message(result)
        self.assertIn("OCR ran", message)
        self.assertNotIn("needs an OCR-capable engine", message)

    def test_a_vision_failure_is_an_engine_error(self):
        source = self.tmp / "broken.png"
        Image.new("RGB", (10, 10), "white").save(source)
        vision = FakeVision([[]])
        vision.VNImageRequestHandler = SimpleNamespace(
            alloc=lambda: SimpleNamespace(
                initWithData_options_=lambda data, options: SimpleNamespace(
                    performRequests_error_=lambda requests, error: (False, "decode failed")
                )
            )
        )
        with self.assertRaisesRegex(EngineError, "decode failed"):
            self.convert(source, vision)

    def test_an_unreadable_file_is_an_engine_error(self):
        source = self.tmp / "not-really.png"
        source.write_bytes(b"not an image")
        with self.assertRaisesRegex(EngineError, "apple-vision failed"):
            self.convert(source, FakeVision([]))

    def test_refuses_other_formats(self):
        self.assertTrue(AppleVisionOcrEngine().can_handle(Path("scan.PDF")))
        self.assertTrue(AppleVisionOcrEngine().can_handle(Path("photo.WebP")))
        self.assertFalse(AppleVisionOcrEngine().can_handle(Path("notes.docx")))
        with self.assertRaisesRegex(EngineError, "only reads PDF and image"):
            AppleVisionOcrEngine().convert(Path("notes.docx"), "none")

    def test_outside_macos_it_says_so_before_reading_anything(self):
        with on_platform("linux"), self.assertRaisesRegex(EngineError, "only on macOS"):
            AppleVisionOcrEngine().convert(self.tmp / "missing.png", "none")

    def test_without_pyobjc_it_names_the_package_to_install(self):
        # objc is stubbed too: importing the real one inside patch.dict would
        # leave it half-unloaded on exit, and PyObjC refuses to load twice.
        objc = SimpleNamespace(autorelease_pool=contextlib.nullcontext)
        with patch.dict(sys.modules, {"objc": objc, "Vision": None}), on_platform("darwin"):
            with self.assertRaisesRegex(EngineError, "pyobjc-framework-Vision"):
                AppleVisionOcrEngine().convert(self.tmp / "missing.png", "none")


if __name__ == "__main__":
    unittest.main()
