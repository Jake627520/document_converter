import tempfile
import unittest
from pathlib import Path
from document_converter.detector import inspect_pdf, _inspect_builtin, PdfProfile
from document_converter.pipeline import choose_engine
from pdf_samples import write_ascii85_text_pdf, write_scanned_pdf, write_text_pdf

def _create_minimal_text_pdf(path: Path, text: str = "Hello World PDF Content Testing Detector"):
    return write_text_pdf(path, text)

def _create_minimal_scanned_pdf(path: Path):
    return write_scanned_pdf(path)

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

    def test_builtin_analyzer_agrees_with_the_optional_library(self):
        """A text PDF must not read as scanned just because pypdf is absent."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            for name, builder in (("digital", write_text_pdf), ("ascii85", write_ascii85_text_pdf)):
                pdf_path = builder(Path(tmp_dir) / f"{name}.pdf")
                with self.subTest(sample=name):
                    builtin = _inspect_builtin(pdf_path, 10)
                    self.assertEqual(builtin.details["analyzer"], "builtin_stream")
                    self.assertTrue(builtin.has_text_layer)
                    self.assertEqual(builtin.classification, "text_based")
                    self.assertEqual(builtin.classification, inspect_pdf(pdf_path).classification)

    def test_builtin_analyzer_reports_no_text_for_an_image_only_pdf(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            pdf_path = write_scanned_pdf(Path(tmp_dir) / "scanned.pdf")
            builtin = _inspect_builtin(pdf_path, 10)
            self.assertEqual(builtin.total_chars, 0)
            self.assertTrue(builtin.is_scanned)
            self.assertEqual(builtin.classification, "scanned")

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
            # The model-free reader stays last: it needs no weights, so it keeps
            # conversion working when every model-based engine is unavailable.
            self.assertEqual(engine_names[-1], "docling-native")

if __name__ == "__main__":
    unittest.main()
