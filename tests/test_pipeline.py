import tempfile
import unittest
from pathlib import Path
from document_converter.pipeline import discover_inputs, choose_engine
from document_converter.detector import PdfProfile

class TestPipeline(unittest.TestCase):
    """Ref: specs/002-engine-adapter.md & specs/005-ocr-detection.md"""

    def test_discover_inputs_single_file(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "doc.pdf"
            file_path.write_bytes(b"%PDF-1.4")
            inputs = discover_inputs(file_path)
            self.assertEqual(inputs, [file_path])

    def test_discover_inputs_directory(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            (root / "a.pdf").write_bytes(b"")
            (root / "b.docx").write_bytes(b"")
            (root / "ignore.exe").write_bytes(b"")
            inputs = discover_inputs(root)
            suffixes = {p.suffix for p in inputs}
            self.assertEqual(suffixes, {".pdf", ".docx"})

    def test_choose_engine_auto_text_pdf(self):
        profile = PdfProfile(path=Path("sample.pdf"), has_text_layer=True, is_scanned=False)
        engines = choose_engine("auto", Path("sample.pdf"), profile=profile)
        self.assertEqual(engines[0].name, "docling")

    def test_choose_engine_auto_scanned_pdf(self):
        profile = PdfProfile(path=Path("scanned.pdf"), has_text_layer=False, is_scanned=True)
        engines = choose_engine("auto", Path("scanned.pdf"), profile=profile)
        engine_names = [e.name for e in engines]
        self.assertEqual(engine_names[0], "docling")
        self.assertIn("mineru", engine_names)
        self.assertIn("marker", engine_names)

if __name__ == "__main__":
    unittest.main()
