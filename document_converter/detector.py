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


def _is_cjk(char: str) -> bool:
    """Check if character belongs to CJK (Chinese, Japanese, Korean) Unicode blocks."""
    cp = ord(char)
    return (
        0x4E00 <= cp <= 0x9FFF or      # CJK Unified Ideographs
        0x3400 <= cp <= 0x4DBF or      # CJK Extension A
        0x20000 <= cp <= 0x2A6DF or    # CJK Extension B
        0xF900 <= cp <= 0xFAFF or      # CJK Compatibility Ideographs
        0x3040 <= cp <= 0x309F or      # Hiragana
        0x30A0 <= cp <= 0x30FF or      # Katakana
        0xAC00 <= cp <= 0xD7AF or      # Hangul Syllables
        0x1100 <= cp <= 0x11FF or      # Hangul Jamo
        0xFF00 <= cp <= 0xFFEF        # Halfwidth and Fullwidth Forms
    )


def inspect_pdf(path: Path, max_sample_pages: int = 10) -> PdfProfile:
    """
    Inspect a PDF file to detect whether it is text-based (has digital text layer)
    or scanned (image-based without extractable text).
    Gracefully uses pypdf/pymupdf if installed, and falls back to a robust built-in
    stream analyzer without requiring external dependencies.
    """
    if not path.is_file():
        return PdfProfile(
            path=path,
            page_count=0,
            total_chars=0,
            has_text_layer=False,
            is_scanned=False,
            classification="unknown",
            details={"analyzer": "none", "error": "file_not_found"},
        )

    try:
        data_head = path.read_bytes()[:1024]
        if len(data_head) == 0:
            return PdfProfile(
                path=path,
                page_count=0,
                total_chars=0,
                has_text_layer=False,
                is_scanned=False,
                classification="unknown",
                details={"analyzer": "none", "error": "empty_file"},
            )
        if b"%PDF-" not in data_head:
            return PdfProfile(
                path=path,
                page_count=0,
                total_chars=0,
                has_text_layer=False,
                is_scanned=False,
                classification="unknown",
                details={"analyzer": "none", "error": "invalid_pdf_header"},
            )
    except Exception as exc:
        return PdfProfile(
            path=path,
            page_count=0,
            total_chars=0,
            has_text_layer=False,
            is_scanned=False,
            classification="unknown",
            details={"analyzer": "none", "error": str(exc)},
        )

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


def _classify(
    page_count: int,
    total_chars: int,
    has_images: bool,
    effective_chars: float | None = None,
) -> tuple[bool, bool, PdfClassification]:
    page_count = max(page_count, 1)
    if effective_chars is None:
        effective_chars = float(total_chars)

    avg_effective = effective_chars / page_count

    if avg_effective >= 25:
        # Clear text layer present
        return True, False, "text_based"
    elif effective_chars < 10:
        # Little to no text
        if has_images:
            return False, True, "scanned"
        # No images and no/little text: ambiguous/blank document
        return False, False, "unknown"
    else:
        # Ambiguous / sparse text
        if has_images:
            return True, True, "hybrid"
        # If there are no images at all and text is present, it is a short text document
        return True, False, "text_based"


def _inspect_with_pypdf(path: Path, max_pages: int) -> PdfProfile:
    import pypdf
    reader = pypdf.PdfReader(str(path))
    page_count = len(reader.pages)
    if page_count == 0:
        return PdfProfile(
            path=path,
            page_count=0,
            total_chars=0,
            has_text_layer=False,
            is_scanned=False,
            classification="unknown",
            details={"analyzer": "pypdf", "sampled_pages": 0},
        )
    sample_pages = min(page_count, max_pages)

    total_chars = 0
    effective_chars = 0.0
    has_images = False

    for i in range(sample_pages):
        page = reader.pages[i]
        text = page.extract_text() or ""
        stripped = text.strip()
        total_chars += len(stripped)
        for c in stripped:
            effective_chars += 2.5 if _is_cjk(c) else 1.0
        if hasattr(page, "images") and len(page.images) > 0:
            has_images = True

    has_text, is_scanned, classification = _classify(
        sample_pages, total_chars, has_images, effective_chars
    )
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
    if page_count == 0:
        return PdfProfile(
            path=path,
            page_count=0,
            total_chars=0,
            has_text_layer=False,
            is_scanned=False,
            classification="unknown",
            details={"analyzer": "pymupdf", "sampled_pages": 0},
        )
    sample_pages = min(page_count, max_pages)

    total_chars = 0
    effective_chars = 0.0
    has_images = False

    for i in range(sample_pages):
        page = doc[i]
        text = page.get_text() or ""
        stripped = text.strip()
        total_chars += len(stripped)
        for c in stripped:
            effective_chars += 2.5 if _is_cjk(c) else 1.0
        if len(page.get_images()) > 0:
            has_images = True

    has_text, is_scanned, classification = _classify(
        sample_pages, total_chars, has_images, effective_chars
    )
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


def _parse_cmap(stream_bytes: bytes) -> dict[str, str]:
    """Parse PostScript ToUnicode CMap beginbfchar mappings."""
    cmap: dict[str, str] = {}
    bfchar_match = re.search(rb"beginbfchar(.*?)endbfchar", stream_bytes, re.DOTALL)
    if bfchar_match:
        for m in re.finditer(rb"<([0-9a-fA-F]+)>\s*<([0-9a-fA-F]+)>", bfchar_match.group(1)):
            code = m.group(1).decode("ascii").upper()
            target_hex = m.group(2).decode("ascii")
            try:
                chars = bytes.fromhex(target_hex).decode("utf-16-be", errors="ignore")
                if chars:
                    cmap[code] = chars
            except Exception:
                pass
    return cmap


def _inspect_builtin(path: Path, max_pages: int) -> PdfProfile:
    try:
        data = path.read_bytes()
    except Exception as exc:
        return PdfProfile(
            path=path,
            page_count=0,
            total_chars=0,
            has_text_layer=False,
            is_scanned=False,
            classification="unknown",
            details={"analyzer": "builtin_stream", "error": str(exc)},
        )

    if len(data) == 0:
        return PdfProfile(
            path=path,
            page_count=0,
            total_chars=0,
            has_text_layer=False,
            is_scanned=False,
            classification="unknown",
            details={"analyzer": "builtin_stream", "error": "empty_file"},
        )

    header_idx = data.find(b"%PDF-")
    if header_idx == -1 or header_idx > 1024:
        return PdfProfile(
            path=path,
            page_count=0,
            total_chars=0,
            has_text_layer=False,
            is_scanned=False,
            classification="unknown",
            details={"analyzer": "builtin_stream", "error": "invalid_pdf_header"},
        )

    # Estimate page count by counting /Type /Page (excluding /Pages)
    page_matches = len(re.findall(rb"/Type\s*/Page\b", data))
    if page_matches == 0 and b"/Catalog" not in data and b"/Pages" not in data and b"/Root" not in data:
        return PdfProfile(
            path=path,
            page_count=0,
            total_chars=0,
            has_text_layer=False,
            is_scanned=False,
            classification="unknown",
            details={"analyzer": "builtin_stream", "error": "corrupted_pdf", "page_matches": 0},
        )

    page_count = max(page_matches, 1)
    has_images = bool(re.search(rb"/Subtype\s*/Image\b", data))

    # Extract text from PDF content streams.
    stream_pattern = re.compile(rb"stream\r?\n(.*?)endstream", re.DOTALL)
    decoded_streams: list[bytes] = []
    cmap: dict[str, str] = {}

    for match in stream_pattern.finditer(data):
        payload = match.group(1)
        for decoded in _decode_stream(payload):
            if b"begincmap" in decoded or b"beginbfchar" in decoded:
                cmap.update(_parse_cmap(decoded))
                break
            if b"BT" in decoded and b"ET" in decoded:
                decoded_streams.append(decoded)
                break

    total_chars = 0
    effective_chars = 0.0

    for decoded in decoded_streams:
        if b"BT" not in decoded and b"Tj" not in decoded and b"TJ" not in decoded:
            continue

        bt_blocks = re.findall(rb"BT\s*(.*?)\s*ET", decoded, re.DOTALL)
        if not bt_blocks:
            bt_blocks = [decoded]

        for block in bt_blocks:
            # 1. Hexadecimal strings <00010002> Tj or [<0001> 10 <0002>] TJ
            for hex_match in re.finditer(rb"<([0-9a-fA-F\s]+)>", block):
                raw_hex = re.sub(rb"\s+", b"", hex_match.group(1)).decode("ascii").upper()
                if len(raw_hex) % 4 == 0:
                    for i in range(0, len(raw_hex), 4):
                        chunk = raw_hex[i : i + 4]
                        char = cmap.get(chunk)
                        if char:
                            total_chars += len(char)
                            for c in char:
                                effective_chars += 2.5 if _is_cjk(c) else 1.0
                        else:
                            try:
                                char = bytes.fromhex(chunk).decode("utf-16-be")
                                total_chars += 1
                                effective_chars += 2.5 if _is_cjk(char) else 1.0
                            except Exception:
                                total_chars += 1
                                effective_chars += 1.0
                elif len(raw_hex) % 2 == 0:
                    for i in range(0, len(raw_hex), 2):
                        chunk = raw_hex[i : i + 2]
                        char = cmap.get(chunk)
                        if char:
                            total_chars += len(char)
                            for c in char:
                                effective_chars += 2.5 if _is_cjk(c) else 1.0
                        else:
                            cp = int(chunk, 16)
                            if 32 <= cp <= 126 or cp in (9, 10, 13) or cp >= 160:
                                total_chars += 1
                                effective_chars += 1.0

            # 2. Literal parenthesized strings (sample text)
            literal_strings = re.findall(rb"\(([^)]+)\)", block)
            for s in literal_strings:
                if s.startswith(b"\xfe\xff"):
                    try:
                        text = s[2:].decode("utf-16-be", errors="ignore")
                        total_chars += len(text)
                        for c in text:
                            effective_chars += 2.5 if _is_cjk(c) else 1.0
                        continue
                    except Exception:
                        pass
                try:
                    text = s.decode("utf-8")
                    chars = [
                        c for c in text
                        if 32 <= ord(c) <= 126 or ord(c) in (9, 10, 13) or _is_cjk(c) or ord(c) >= 160
                    ]
                    total_chars += len(chars)
                    for c in chars:
                        effective_chars += 2.5 if _is_cjk(c) else 1.0
                except UnicodeDecodeError:
                    chars = [c for c in s if 32 <= c <= 126 or c in (9, 10, 13)]
                    total_chars += len(chars)
                    effective_chars += float(len(chars))

    has_text, is_scanned, classification = _classify(
        page_count, total_chars, has_images, effective_chars
    )
    return PdfProfile(
        path=path,
        page_count=page_count,
        total_chars=total_chars,
        has_text_layer=has_text,
        is_scanned=is_scanned,
        classification=classification,
        details={"analyzer": "builtin_stream", "page_matches": page_matches},
    )
