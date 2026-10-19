"""Regression: UTF-8-only text path and TextDirectEngine."""

from pathlib import Path
import unittest

from document_converter.engines.text_direct_engine import TextDirectEngine
from document_converter.engines.base import EngineError
from document_converter.pipeline import convert_one, choose_engine


class TextDirectEngineTests(unittest.TestCase):
    def test_reads_utf8_markdown(self):
        path = Path(self.enterContext(__import__("tempfile").TemporaryDirectory())) / "a.md"
        path.write_text("# Title\n\nHello **world**\n", encoding="utf-8")
        result = TextDirectEngine().convert(path, "none")
        self.assertEqual(result.engine, "text_direct")
        self.assertIn("# Title", result.markdown)
        self.assertTrue(result.text)

    def test_reads_utf8_txt_without_stripping_hashes(self):
        path = Path(self.enterContext(__import__("tempfile").TemporaryDirectory())) / "a.txt"
        path.write_text("#1 priority\n- 5 units\n", encoding="utf-8")
        result = TextDirectEngine().convert(path, "none")
        self.assertEqual(result.text, "#1 priority\n- 5 units\n")

    def test_rejects_utf16(self):
        path = Path(self.enterContext(__import__("tempfile").TemporaryDirectory())) / "u.txt"
        path.write_bytes("Hello".encode("utf-16"))
        with self.assertRaises(EngineError) as ctx:
            TextDirectEngine().convert(path, "none")
        self.assertIn("UTF-8", str(ctx.exception))

    def test_rejects_big5(self):
        path = Path(self.enterContext(__import__("tempfile").TemporaryDirectory())) / "b.txt"
        path.write_bytes("中文".encode("big5"))
        with self.assertRaises(EngineError) as ctx:
            TextDirectEngine().convert(path, "none")
        self.assertIn("UTF-8", str(ctx.exception))

    def test_auto_prefers_text_direct_for_md(self):
        path = Path("note.md")
        chain = choose_engine("auto", path)
        self.assertEqual(len(chain), 1)
        self.assertEqual(chain[0].name, "text_direct")

    def test_convert_one_surfaces_encoding_error(self):
        path = Path(self.enterContext(__import__("tempfile").TemporaryDirectory())) / "bad.txt"
        path.write_bytes(b"\xff\xfe\x00\x01")
        with self.assertRaises(EngineError) as ctx:
            convert_one(path, "auto", "none")
        message = str(ctx.exception)
        self.assertIn("UTF-8", message)
        self.assertNotIn("Docling is not installed", message)


if __name__ == "__main__":
    unittest.main()
