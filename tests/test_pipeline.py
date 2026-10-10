import tempfile
import unittest
from pathlib import Path
from document_converter.pipeline import discover_inputs, choose_engine
from document_converter.detector import PdfProfile
from document_converter.engines.base import EngineError

class TestPipeline(unittest.TestCase):
    """Ref: openspec/specs/engine-adapter/spec.md & openspec/specs/pdf-detection/spec.md"""

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

    def test_choose_engine_auto_pdf_ends_with_the_model_free_reader(self):
        """PDF conversion must stay possible without model weights installed."""
        profile = PdfProfile(path=Path("sample.pdf"), has_text_layer=True, is_scanned=False)
        for engines in (
            choose_engine("auto", Path("sample.pdf"), profile=profile),
            choose_engine("auto", Path("sample.pdf"), profile=None),
        ):
            self.assertEqual([e.name for e in engines][-1], "docling-native")

    def test_choose_engine_explicit_model_free_reader_rejects_non_pdf(self):
        engines = choose_engine("docling-native", Path("sample.pdf"))
        self.assertEqual([e.name for e in engines], ["docling-native"])
        with self.assertRaises(EngineError):
            choose_engine("docling-native", Path("notes.md"))

    def test_choose_engine_auto_image_excludes_the_pdf_only_reader(self):
        engines = choose_engine("auto", Path("scan.png"))
        self.assertNotIn("docling-native", [e.name for e in engines])

    def test_choose_engine_auto_scanned_pdf(self):
        profile = PdfProfile(path=Path("scanned.pdf"), has_text_layer=False, is_scanned=True)
        engines = choose_engine("auto", Path("scanned.pdf"), profile=profile)
        engine_names = [e.name for e in engines]
        self.assertEqual(engine_names[0], "docling")
        self.assertIn("mineru", engine_names)
        self.assertIn("marker", engine_names)

if __name__ == "__main__":
    unittest.main()
