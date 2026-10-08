import tempfile
import unittest
from pathlib import Path
from document_converter.models import ConversionResult
from document_converter.writer import write_result

class TestWriter(unittest.TestCase):
    def test_write_markdown(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            src = tmp_path / "a.pdf"
            src.write_bytes(b"")
            result = ConversionResult(source=src, engine="test", markdown="# Hello\n", text="Hello\n")
            write_result(result, tmp_path / "out", ["md"])
            self.assertEqual((tmp_path / "out" / "a.md").read_text(), "# Hello\n")

    def test_html_fallback(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            src = tmp_path / "a.pdf"
            src.write_bytes(b"")
            result = ConversionResult(source=src, engine="test", markdown="# Hello\n")
            write_result(result, tmp_path / "out", ["html"])
            html = (tmp_path / "out" / "a.html").read_text()
            self.assertIn("<title>a</title>", html)

if __name__ == "__main__":
    unittest.main()
