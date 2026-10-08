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
            self.assertIn("<h1>Hello</h1>", html)
            self.assertIn("<style>", html)

    def test_html_fallback_renders_tables_lists_and_escapes_html(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            src = tmp_path / "a.pdf"
            src.write_bytes(b"")
            md = "| H |\n| --- |\n| <script> |\n\n- item"
            result = ConversionResult(source=src, engine="test", markdown=md)
            write_result(result, tmp_path / "out", ["html"])
            html = (tmp_path / "out" / "a.html").read_text()
            self.assertIn("<table>", html)
            self.assertIn("<ul><li>item</li></ul>", html)
            self.assertIn("&lt;script&gt;", html)
            self.assertNotIn("<script>", html)

    def test_native_html_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            src = tmp_path / "a.pdf"
            src.write_bytes(b"")
            native_html = "<html><body>native</body></html>"
            result = ConversionResult(source=src, engine="test", markdown="# fallback", html=native_html)
            write_result(result, tmp_path / "out", ["html"])
            self.assertEqual((tmp_path / "out" / "a.html").read_text(), native_html)

    def test_empty_markdown_still_writes_html_document(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            src = tmp_path / "a.pdf"
            src.write_bytes(b"")
            result = ConversionResult(source=src, engine="test", markdown="")
            write_result(result, tmp_path / "out", ["html"])
            html = (tmp_path / "out" / "a.html").read_text()
            self.assertIn("<!doctype html>", html)
            self.assertEqual(result.warnings, [])

if __name__ == "__main__":
    unittest.main()
