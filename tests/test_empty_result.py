import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from document_converter.models import ConversionResult
from document_converter.pipeline import _process_single_item, process_batch


class TestEmptyResultHandling(unittest.TestCase):
    """Verify that CLI/pipeline does not write empty or text-free output files."""

    def test_empty_md_does_not_write_output_files(self):
        """Empty .md file must fail and not write any output file."""
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            src = temp_path / "empty.md"
            src.write_text("", encoding="utf-8")
            out_dir = temp_path / "out"

            res = _process_single_item(
                path=src,
                output_dir=out_dir,
                formats=["md", "html", "txt"],
                engine_name="auto",
                image_mode="none",
                clean=False,
                preserve_layout=False,
                source_root=temp_path,
                output_stem="empty",
            )

            self.assertFalse(res["success"])
            self.assertIn("no text recovered", res["error"])
            self.assertFalse(out_dir.exists() and any(out_dir.iterdir()))

    def test_whitespace_only_txt_is_refused(self):
        """Whitespace-only .txt file must fail and not write any output file."""
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            src = temp_path / "blank.txt"
            src.write_text("  \n\n\t  ", encoding="utf-8")
            out_dir = temp_path / "out"

            res = _process_single_item(
                path=src,
                output_dir=out_dir,
                formats=["md", "html", "txt"],
                engine_name="auto",
                image_mode="none",
                clean=False,
                preserve_layout=False,
                source_root=temp_path,
                output_stem="blank",
            )

            self.assertFalse(res["success"])
            self.assertIn("no text recovered", res["error"])
            self.assertFalse(out_dir.exists() and any(out_dir.iterdir()))

    def test_batch_continues_after_empty_file(self):
        """A batch containing an empty file and a valid file processes both without aborting."""
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            empty_file = temp_path / "empty.md"
            empty_file.write_text("", encoding="utf-8")
            valid_file = temp_path / "valid.md"
            valid_file.write_text("# Hello World\nValid text.", encoding="utf-8")
            out_dir = temp_path / "out"

            results = process_batch(
                inputs=[empty_file, valid_file],
                output_dir=out_dir,
                formats=["md"],
                engine_name="auto",
                image_mode="none",
                clean=False,
                preserve_layout=False,
                source_root=temp_path,
            )

            self.assertEqual(len(results), 2)
            results_by_path = {r["path"].name: r for r in results}

            empty_res = results_by_path["empty.md"]
            self.assertFalse(empty_res["success"])
            self.assertIn("no text recovered", empty_res["error"])
            self.assertFalse((out_dir / "empty.md").exists())

            valid_res = results_by_path["valid.md"]
            self.assertTrue(valid_res["success"])
            self.assertTrue((out_dir / "valid.md").exists())
            self.assertIn("Hello World", (out_dir / "valid.md").read_text(encoding="utf-8"))

    def test_non_empty_md_still_writes(self):
        """Non-empty markdown writes output files normally."""
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            src = temp_path / "doc.md"
            src.write_text("# Title\nContent", encoding="utf-8")
            out_dir = temp_path / "out"

            res = _process_single_item(
                path=src,
                output_dir=out_dir,
                formats=["md", "html"],
                engine_name="auto",
                image_mode="none",
                clean=False,
                preserve_layout=False,
                source_root=temp_path,
                output_stem="doc",
            )

            self.assertTrue(res["success"])
            self.assertTrue((out_dir / "doc.md").exists())
            self.assertTrue((out_dir / "doc.html").exists())

    def test_image_placeholder_only_does_not_write_files(self):
        """A conversion result with only image comment placeholders counts as no recovered text."""
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            src = temp_path / "scan.pdf"
            src.write_bytes(b"%PDF-1.4")
            out_dir = temp_path / "out"

            mock_res = ConversionResult(
                source=src,
                engine="docling",
                markdown="<!-- image -->\n<!-- image -->\n",
            )

            with patch("document_converter.pipeline.convert_one", return_value=mock_res):
                res = _process_single_item(
                    path=src,
                    output_dir=out_dir,
                    formats=["md"],
                    engine_name="auto",
                    image_mode="none",
                    clean=False,
                    preserve_layout=False,
                    source_root=temp_path,
                    output_stem="scan",
                )

                self.assertFalse(res["success"])
                self.assertIn("no text recovered", res["error"])
                self.assertIn("OCR", res["error"])
                self.assertFalse((out_dir / "scan.md").exists())


if __name__ == "__main__":
    unittest.main()
