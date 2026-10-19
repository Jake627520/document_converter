import os
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch

from pdf_samples import write_text_pdf

try:
    from typer.testing import CliRunner
    from document_converter.cli import app
    HAS_TYPER = True
except ImportError:
    HAS_TYPER = False

@unittest.skipUnless(HAS_TYPER, "typer not installed in current environment")
class TestCli(unittest.TestCase):
    """Ref: openspec/specs/cli-interface/spec.md"""

    def setUp(self):
        self.runner = CliRunner()

    def test_help_command(self):
        result = self.runner.invoke(app, ["--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Convert local documents", result.output)

    def test_list_engines_command(self):
        result = self.runner.invoke(app, ["list-engines"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("text_direct", result.output)
        self.assertIn("docling", result.output)
        self.assertIn("marker", result.output)
        self.assertIn("mineru", result.output)

    def test_list_engines_detects_mineru_by_the_command_the_adapter_runs(self):
        from unittest import mock

        def listing(installed):
            with mock.patch("shutil.which", side_effect=lambda name: f"/stub/{name}" if name in installed else None):
                return self.runner.invoke(app, ["list-engines"]).output

        def mineru_line(installed):
            return next(line for line in listing(installed).splitlines() if line.startswith("mineru"))

        self.assertIn("not detected", mineru_line({"mineru"}))
        self.assertIn("installed", mineru_line({"mineru-kit"}))
        # The install command stays on its row: wrapped, its second half reads as another command.
        self.assertIn("pip install 'mineru>=4,<5'", mineru_line(set()))

    def test_convert_accepts_text_direct_engine(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "notes.md"
            source.write_text("# Direct Title\n", encoding="utf-8")
            result = self.runner.invoke(
                app, ["convert", str(source), "--engine", "text_direct", "-o", str(Path(temp) / "out")]
            )
        self.assertEqual(result.exit_code, 0)
        self.assertNotIn("engine must be", result.output)

    def test_inspect_text_pdf(self):
        with tempfile.TemporaryDirectory() as temp:
            sample = write_text_pdf(Path(temp) / "sample_text.pdf")
            result = self.runner.invoke(app, ["inspect", str(sample)])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("sample_text.pdf", result.output)
        self.assertIn("text_based", result.output)

    def test_inspect_directory_shows_distinguishable_relative_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "input"
            (root / "department-a").mkdir(parents=True)
            (root / "department-b").mkdir()
            write_text_pdf(root / "department-a" / "statement.pdf")
            write_text_pdf(root / "department-b" / "statement.pdf")

            # Widen the console so the table does not wrap the path column.
            with patch.dict(os.environ, {"COLUMNS": "200"}):
                result = self.runner.invoke(app, ["inspect", str(root)])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("department-a/statement.pdf", result.output)
        self.assertIn("department-b/statement.pdf", result.output)

    def test_list_engines_reports_the_model_free_pdf_engine(self):
        result = self.runner.invoke(app, ["list-engines"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("docling-native", result.output)

    def test_convert_accepts_the_model_free_pdf_engine(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "notes.md"
            source.write_text("# Title\n", encoding="utf-8")
            result = self.runner.invoke(
                app, ["convert", str(source), "--engine", "docling-native", "-o", str(Path(temp) / "out")]
            )
        self.assertEqual(result.exit_code, 0)
        self.assertNotIn("engine must be", result.output)

    def test_convert_rejects_an_unknown_engine(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "notes.md"
            source.write_text("# Title\n", encoding="utf-8")
            result = self.runner.invoke(app, ["convert", str(source), "--engine", "nope"])
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("docling-native", result.output)

if __name__ == "__main__":
    unittest.main()
