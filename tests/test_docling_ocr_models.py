"""Docling's full install reading a scan and a photo with its own OCR models.

Collected only where REQUIRE_DOCLING_MODELS is set (see conftest.py): Docling
downloads its layout model from Hugging Face and RapidOCR its recognition
models on first use, and the other jobs stay offline on purpose.
"""
import tempfile
import unittest
from pathlib import Path

from document_converter.pipeline import convert_one
from ocr_samples import CHINESE, ENGLISH, page, squeezed


class DoclingModelOcrTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def assert_read_back(self, result):
        self.assertEqual(result.engine, "docling")
        text = squeezed(result.markdown)
        self.assertIn(squeezed(ENGLISH).lower(), text.lower())
        self.assertIn(CHINESE, text)

    def test_reads_a_scanned_pdf(self):
        source = self.tmp / "scan.pdf"
        page().save(source, resolution=200)
        result = convert_one(source, "auto", "none")
        self.assertEqual(result.metadata["pdf_profile"].classification, "scanned")
        self.assert_read_back(result)

    def test_reads_a_photo(self):
        source = self.tmp / "photo.png"
        page().save(source)
        self.assert_read_back(convert_one(source, "auto", "none"))


if __name__ == "__main__":
    unittest.main()
