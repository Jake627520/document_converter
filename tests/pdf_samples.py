"""Synthetic PDF builders shared by the tests.

The repository .gitignore excludes ``*.pdf`` so real documents cannot be
committed by accident, which also means no PDF fixture can live in the tree.
These builders write small but structurally valid PDFs - correct cross-reference
offsets, a font resource and a real content stream - so both ``pypdf`` and the
built-in stream analyzer in ``document_converter.detector`` read them the same
way. Tests create them in a temporary directory.
"""
import base64
import zlib
from pathlib import Path

TEXT_SAMPLE = (
    "This is a digital PDF document with readable text stream content used by the converter tests."
)


def _assemble(objects: list[bytes]) -> bytes:
    """Serialize numbered PDF objects with a correct xref table and trailer."""
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{number} 0 obj\n".encode("ascii") + body + b"\nendobj\n"
    xref_offset = len(out)
    out += f"xref\n0 {len(objects) + 1}\n".encode("ascii")
    out += b"0000000000 65535 f \n"
    for offset in offsets:
        out += f"{offset:010d} 00000 n \n".encode("ascii")
    out += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    return bytes(out)


def _page_objects(contents: bytes, resources: bytes) -> list[bytes]:
    return [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources "
        + resources
        + b" /Contents 4 0 R >>",
        contents,
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]


def _content_stream(text: str) -> bytes:
    body = f"BT /F1 12 Tf 72 712 Td ({text}) Tj ET\n".encode("latin1")
    compressed = zlib.compress(body)
    return (
        b"<< /Length "
        + str(len(compressed)).encode("ascii")
        + b" /Filter /FlateDecode >>\nstream\n"
        + compressed
        + b"\nendstream"
    )


def _ascii85_content_stream(text: str) -> bytes:
    """A content stream encoded the way several generators emit it.

    ASCII85 wrapping Flate, and `endstream` directly after the payload with no
    separating end-of-line, which is what the built-in analyzer has to tolerate.
    """
    body = f"BT /F1 12 Tf 72 712 Td ({text}) Tj ET\n".encode("latin1")
    payload = base64.a85encode(zlib.compress(body), adobe=True)[2:]  # drop the leading <~
    return (
        b"<< /Length "
        + str(len(payload)).encode("ascii")
        + b" /Filter [/ASCII85Decode /FlateDecode] >>\nstream\n"
        + payload
        + b"endstream"
    )


def write_text_pdf(path: Path, text: str = TEXT_SAMPLE) -> Path:
    """A single-page PDF whose text layer any analyzer can read."""
    path.write_bytes(_assemble(_page_objects(_content_stream(text), b"<< /Font << /F1 5 0 R >> >>")))
    return path


def write_ascii85_text_pdf(path: Path, text: str = TEXT_SAMPLE) -> Path:
    """A text PDF using ASCII85+Flate and no EOL before `endstream`."""
    path.write_bytes(
        _assemble(_page_objects(_ascii85_content_stream(text), b"<< /Font << /F1 5 0 R >> >>"))
    )
    return path


def write_scanned_pdf(path: Path) -> Path:
    """A single-page PDF holding only an image XObject and no text operator."""
    image_data = zlib.compress(b"\x00" * 300)
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources "
        b"<< /XObject << /Im1 5 0 R >> >> /Contents 4 0 R >>",
        b"<< /Length 32 >>\nstream\nq 612 0 0 792 0 0 cm /Im1 Do Q\nendstream",
        b"<< /Type /XObject /Subtype /Image /Width 10 /Height 10 /ColorSpace /DeviceGray "
        b"/BitsPerComponent 8 /Length " + str(len(image_data)).encode("ascii")
        + b" /Filter /FlateDecode >>\nstream\n" + image_data + b"\nendstream",
    ]
    path.write_bytes(_assemble(objects))
    return path
