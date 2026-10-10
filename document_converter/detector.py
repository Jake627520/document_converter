import base64
import re
import zlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

PdfClassification = Literal["text_based", "scanned", "hybrid", "unknown"]

@dataclass
class PdfProfile:
    path: Path
    page_count: int = 0
    total_chars: int = 0
    has_text_layer: bool = False
    is_scanned: bool = False
    classification: PdfClassification = "unknown"
    details: dict = field(default_factory=dict)

    @property
    def avg_chars_per_page(self) -> float:
        if self.page_count <= 0:
            return 0.0
        return self.total_chars / self.page_count

def inspect_pdf(path: Path, max_sample_pages: int = 10) -> PdfProfile:
    """
    Inspect a PDF file to detect whether it is text-based (has digital text layer)
    or scanned (image-based without extractable text).
    Gracefully uses pypdf/pymupdf if installed, and falls back to a robust built-in
    stream analyzer without requiring external dependencies.
    """
    # 1. Try pypdf if available
    try:
        import pypdf
        return _inspect_with_pypdf(path, max_sample_pages)
    except Exception:
        pass

    # 2. Try fitz (PyMuPDF) if available
    try:
        import fitz
        return _inspect_with_fitz(path, max_sample_pages)
    except Exception:
        pass

    # 3. Built-in zero-dependency stream analyzer
    return _inspect_builtin(path, max_sample_pages)

def _classify(page_count: int, total_chars: int, has_images: bool) -> tuple[bool, bool, PdfClassification]:
    page_count = max(page_count, 1)
    avg_chars = total_chars / page_count

    if avg_chars >= 25:
        # Clear text layer present
        return True, False, "text_based"
    elif total_chars < 10:
        # Little to no text
        if has_images or total_chars == 0:
            return False, True, "scanned"
        return False, False, "unknown"
    else:
        # Ambiguous / sparse text
        return True, True, "hybrid"

def _inspect_with_pypdf(path: Path, max_pages: int) -> PdfProfile:
    import pypdf
    reader = pypdf.PdfReader(str(path))
    page_count = len(reader.pages)
    sample_pages = min(page_count, max_pages)

    total_chars = 0
    has_images = False

    for i in range(sample_pages):
        page = reader.pages[i]
        text = page.extract_text() or ""
        total_chars += len(text.strip())
        if hasattr(page, "images") and len(page.images) > 0:
            has_images = True

    has_text, is_scanned, classification = _classify(sample_pages, total_chars, has_images)
    return PdfProfile(
        path=path,
        page_count=page_count,
        total_chars=total_chars,
        has_text_layer=has_text,
        is_scanned=is_scanned,
        classification=classification,
        details={"analyzer": "pypdf", "sampled_pages": sample_pages},
    )

def _inspect_with_fitz(path: Path, max_pages: int) -> PdfProfile:
    import fitz
    doc = fitz.open(str(path))
    page_count = len(doc)
    sample_pages = min(page_count, max_pages)

    total_chars = 0
    has_images = False

    for i in range(sample_pages):
        page = doc[i]
        text = page.get_text() or ""
        total_chars += len(text.strip())
        if len(page.get_images()) > 0:
            has_images = True

    has_text, is_scanned, classification = _classify(sample_pages, total_chars, has_images)
    return PdfProfile(
        path=path,
        page_count=page_count,
        total_chars=total_chars,
        has_text_layer=has_text,
        is_scanned=is_scanned,
        classification=classification,
        details={"analyzer": "pymupdf", "sampled_pages": sample_pages},
    )

def _ascii85_decode(payload: bytes) -> bytes:
    stripped = payload.strip()
    if not stripped.startswith(b"<~"):
        stripped = b"<~" + stripped
    if not stripped.endswith(b"~>"):
        stripped = stripped + b"~>"
    return base64.a85decode(stripped, adobe=True, ignorechars=b" \t\r\n\x0b\x0c")


def _decode_stream(stream_bytes: bytes) -> list[bytes]:
    """Return plausible decodings of one content stream, best candidate first.

    The built-in analyzer reads the raw file without a PDF object parser, so the
    stream's /Filter entry is not available here. Instead each common text-stream
    encoding is attempted and the caller keeps whichever decoding exposes a
    `BT`/`ET` text block: stored, FlateDecode, ASCII85Decode, and ASCII85 wrapping
    Flate, which is what several generators emit.
    """
    candidates: list[bytes] = []
    for payload in dict.fromkeys((stream_bytes.strip(b"\r\n"), stream_bytes)):
        candidates.append(payload)
        try:
            candidates.append(zlib.decompress(payload))
        except Exception:
            pass
        try:
            unascii = _ascii85_decode(payload)
        except Exception:
            continue
        candidates.append(unascii)
        try:
            candidates.append(zlib.decompress(unascii))
        except Exception:
            pass
    return candidates


def _inspect_builtin(path: Path, max_pages: int) -> PdfProfile:
    data = path.read_bytes()

    # Estimate page count by counting /Type /Page (excluding /Pages)
    page_matches = len(re.findall(rb"/Type\s*/Page\b", data))
    page_count = max(page_matches, 1)

    has_images = bool(re.search(rb"/Subtype\s*/Image\b", data))

    # Extract text from PDF content streams. The closing keyword is not required to
    # sit on its own line: many producers write the stream bytes and `endstream`
    # without an intervening EOL.
    stream_pattern = re.compile(rb"stream\r?\n(.*?)endstream", re.DOTALL)
    total_chars = 0

    for match in stream_pattern.finditer(data):
        for decoded in _decode_stream(match.group(1)):
            # Look for PDF text show operators: (text) Tj, [(t) 10 (ext)] TJ, ' or "
            # Or look for Begin Text (BT) ... End Text (ET) blocks
            if b"BT" not in decoded or b"ET" not in decoded:
                continue
            # Extract parenthesized strings: (sample text)
            literal_strings = re.findall(rb"\(([^)]+)\)", decoded)
            for s in literal_strings:
                # filter out non-printable ASCII noise
                chars = [c for c in s if 32 <= c <= 126 or c in (9, 10, 13)]
                total_chars += len(chars)
            break

    has_text, is_scanned, classification = _classify(page_count, total_chars, has_images)
    return PdfProfile(
        path=path,
        page_count=page_count,
        total_chars=total_chars,
        has_text_layer=has_text,
        is_scanned=is_scanned,
        classification=classification,
        details={"analyzer": "builtin_stream", "page_matches": page_matches},
    )
