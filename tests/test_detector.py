import tempfile
import unittest
from pathlib import Path
from document_converter.detector import inspect_pdf, _inspect_builtin, PdfProfile
from document_converter.pipeline import choose_engine
from pdf_samples import (
    write_ascii85_text_pdf,
    write_corrupt_pdf,
    write_empty_pdf,
    write_japanese_pdf,
    write_korean_pdf,
    write_scanned_pdf,
    write_simplified_chinese_pdf,
    write_sparse_text_with_image_pdf,
    write_text_pdf,
    write_traditional_chinese_pdf,
)

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

    def test_detect_traditional_chinese_pdf(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            pdf_path = write_traditional_chinese_pdf(Path(tmp_dir) / "tc.pdf")
            profile = inspect_pdf(pdf_path)
            self.assertTrue(profile.has_text_layer)
            self.assertFalse(profile.is_scanned)
            self.assertEqual(profile.classification, "text_based")
            self.assertGreaterEqual(profile.total_chars, 10)

            builtin = _inspect_builtin(pdf_path, 10)
            self.assertTrue(builtin.has_text_layer)
            self.assertFalse(builtin.is_scanned)
            self.assertEqual(builtin.classification, "text_based")

    def test_detect_simplified_chinese_pdf(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            pdf_path = write_simplified_chinese_pdf(Path(tmp_dir) / "sc.pdf")
            profile = inspect_pdf(pdf_path)
            self.assertTrue(profile.has_text_layer)
            self.assertFalse(profile.is_scanned)
            self.assertEqual(profile.classification, "text_based")

            builtin = _inspect_builtin(pdf_path, 10)
            self.assertTrue(builtin.has_text_layer)
            self.assertFalse(builtin.is_scanned)
            self.assertEqual(builtin.classification, "text_based")

    def test_detect_japanese_and_korean_pdf(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            for name, builder in (("ja.pdf", write_japanese_pdf), ("ko.pdf", write_korean_pdf)):
                pdf_path = builder(Path(tmp_dir) / name)
                with self.subTest(lang=name):
                    profile = inspect_pdf(pdf_path)
                    self.assertTrue(profile.has_text_layer)
                    self.assertFalse(profile.is_scanned)
                    self.assertEqual(profile.classification, "text_based")

                    builtin = _inspect_builtin(pdf_path, 10)
                    self.assertTrue(builtin.has_text_layer)
                    self.assertFalse(builtin.is_scanned)
                    self.assertEqual(builtin.classification, "text_based")

    def test_detect_scanned_pdf(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            pdf_path = Path(tmp_dir) / "scanned.pdf"
            _create_minimal_scanned_pdf(pdf_path)
            profile = inspect_pdf(pdf_path)
            self.assertFalse(profile.has_text_layer)
            self.assertTrue(profile.is_scanned)
            self.assertEqual(profile.classification, "scanned")
            self.assertEqual(profile.total_chars, 0)

    def test_detect_sparse_text_with_image_is_not_clean_text_based(self):
        """A scanned page with stray noise or a page number must not be called text_based."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            pdf_path = write_sparse_text_with_image_pdf(Path(tmp_dir) / "sparse.pdf", "1")
            profile = inspect_pdf(pdf_path)
            self.assertNotEqual(profile.classification, "text_based")
            self.assertTrue(profile.is_scanned)

            builtin = _inspect_builtin(pdf_path, 10)
            self.assertNotEqual(builtin.classification, "text_based")
            self.assertTrue(builtin.is_scanned)

    def test_detect_corrupt_and_empty_pdf_is_unknown_not_scanned(self):
        """Corrupt or 0-byte files must not be diagnosed as scanned documents."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            empty_path = write_empty_pdf(Path(tmp_dir) / "empty.pdf")
            empty_prof = inspect_pdf(empty_path)
            self.assertEqual(empty_prof.classification, "unknown")
            self.assertFalse(empty_prof.is_scanned)
            self.assertFalse(empty_prof.has_text_layer)

            empty_builtin = _inspect_builtin(empty_path, 10)
            self.assertEqual(empty_builtin.classification, "unknown")
            self.assertFalse(empty_builtin.is_scanned)
            self.assertFalse(empty_builtin.has_text_layer)

            corrupt_path = write_corrupt_pdf(Path(tmp_dir) / "corrupt.pdf")
            corrupt_prof = inspect_pdf(corrupt_path)
            self.assertEqual(corrupt_prof.classification, "unknown")
            self.assertFalse(corrupt_prof.is_scanned)
            self.assertFalse(corrupt_prof.has_text_layer)

            corrupt_builtin = _inspect_builtin(corrupt_path, 10)
            self.assertEqual(corrupt_builtin.classification, "unknown")
            self.assertFalse(corrupt_builtin.is_scanned)
            self.assertFalse(corrupt_builtin.has_text_layer)

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

