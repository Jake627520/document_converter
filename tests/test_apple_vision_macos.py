"""apple-vision against the real Vision framework; collected only on macOS."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# Loaded at collection, before tests/test_apple_vision.py swaps stand-ins into
# sys.modules: PyObjC cannot be imported a second time in one process.
import objc  # noqa: F401
import Vision  # noqa: F401

from document_converter.engines.apple_vision_engine import AppleVisionOcrEngine
from document_converter.engines.base import EngineError
from document_converter.pipeline import convert_one
from ocr_samples import CHINESE, ENGLISH, page, squeezed


class RealVisionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def assert_read_back(self, result):
        text = squeezed(result.markdown)
        self.assertIn(squeezed(ENGLISH).lower(), text.lower())
        self.assertIn(CHINESE, text)
        # Two paragraphs drawn far apart stay two paragraphs.
        self.assertGreaterEqual(result.markdown.count("\n\n"), 1)

    def test_reads_english_and_traditional_chinese_from_a_photo(self):
        source = self.tmp / "photo.png"
        page().save(source)
        result = AppleVisionOcrEngine().convert(source, "none")
        self.assertEqual(result.engine, "apple-vision")
        self.assert_read_back(result)

    def test_auto_reads_a_scanned_pdf_with_no_other_ocr_installed(self):
        source = self.tmp / "scan.pdf"
        page().save(source, resolution=200)
        # Whatever else this Mac has installed, the engines auto tries first
        # behave as if absent.
        absent = EngineError("not installed")
        with patch("document_converter.pipeline.DoclingEngine.convert", side_effect=absent), patch(
            "document_converter.pipeline.MarkerEngine.convert", side_effect=absent
        ), patch("document_converter.pipeline.MinerUEngine.convert", side_effect=absent):
            result = convert_one(source, "auto", "none")
        self.assertEqual(result.engine, "apple-vision")
        self.assertEqual(result.metadata["pdf_profile"].classification, "scanned")
        self.assert_read_back(result)


if __name__ == "__main__":
    unittest.main()
