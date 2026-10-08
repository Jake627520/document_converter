import tempfile
import unittest
import zlib
from pathlib import Path
from document_converter.detector import inspect_pdf, PdfProfile
from document_converter.pipeline import choose_engine

def _create_minimal_text_pdf(path: Path, text: str = "Hello World PDF Content Testing Detector"):
    # Minimal valid single-page PDF with text stream
    stream_content = f"BT /F1 12 Tf 72 712 Td ({text}) Tj ET\n".encode("latin1")
    compressed = zlib.compress(stream_content)
    
    pdf_bytes = (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>\nendobj\n"
        b"4 0 obj\n<< /Length " + str(len(compressed)).encode() + b" /Filter /FlateDecode >>\nstream\n"
        + compressed +
        b"\nendstream\nendobj\n"
        b"xref\n0 5\n0000000000 65535 f \n"
        b"trailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n99\n%%EOF\n"
    )
    path.write_bytes(pdf_bytes)

def _create_minimal_scanned_pdf(path: Path):
    # Minimal single-page PDF with an Image XObject and NO text operator
    image_data = zlib.compress(b"\x00" * 100)
    pdf_bytes = (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /XObject << /Im1 4 0 R >> >> >>\nendobj\n"
        b"4 0 obj\n<< /Type /XObject /Subtype /Image /Width 10 /Height 10 /ColorSpace /DeviceRGB /BitsPerComponent 8 /Length "
        + str(len(image_data)).encode() + b" /Filter /FlateDecode >>\nstream\n"
        + image_data +
        b"\nendstream\nendobj\n"
        b"xref\n0 5\n0000000000 65535 f \n"
        b"trailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n99\n%%EOF\n"
    )
    path.write_bytes(pdf_bytes)

class TestPdfDetector(unittest.TestCase):
    def test_detect_text_based_pdf(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            pdf_path = Path(tmp_dir) / "digital.pdf"
            _create_minimal_text_pdf(pdf_path, "This is a digital PDF document with readable text stream.")
            profile = inspect_pdf(pdf_path)
            self.assertTrue(profile.has_text_layer)
            self.assertFalse(profile.is_scanned)
            self.assertEqual(profile.classification, "text_based")
            self.assertGreater(profile.total_chars, 20)

    def test_detect_scanned_pdf(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            pdf_path = Path(tmp_dir) / "scanned.pdf"
            _create_minimal_scanned_pdf(pdf_path)
            profile = inspect_pdf(pdf_path)
            self.assertFalse(profile.has_text_layer)
            self.assertTrue(profile.is_scanned)
            self.assertEqual(profile.classification, "scanned")
            self.assertEqual(profile.total_chars, 0)

    def test_choose_engine_prioritizes_ocr_for_scanned(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            pdf_path = Path(tmp_dir) / "scanned.pdf"
            _create_minimal_scanned_pdf(pdf_path)
            profile = inspect_pdf(pdf_path)
            
            engines = choose_engine("auto", pdf_path, profile=profile)
            engine_names = [e.name for e in engines]
            # Docling is primary, followed by OCR fallback engines
            self.assertEqual(engine_names[0], "docling")
            self.assertIn("mineru", engine_names)
            self.assertIn("marker", engine_names)

if __name__ == "__main__":
    unittest.main()
