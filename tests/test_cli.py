import sys
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

    def test_list_engines_reports_the_office_reader_and_macos_ocr(self):
        result = self.runner.invoke(app, ["list-engines"])
        self.assertEqual(result.exit_code, 0)
        lines = {line.split()[0]: line for line in result.output.splitlines() if line.strip()}
        self.assertIn("format-office", lines["docling-office"])
        self.assertIn("pyobjc-framework-Vision", lines["apple-vision"])
        if sys.platform != "darwin":
            self.assertIn("not detected", lines["apple-vision"])

    def test_convert_accepts_the_new_engine_names(self):
        for engine in ("docling-office", "apple-vision"):
            with self.subTest(engine=engine), tempfile.TemporaryDirectory() as temp:
                source = Path(temp) / "notes.md"
                source.write_text("# Title\n", encoding="utf-8")
                result = self.runner.invoke(app, ["convert", str(source), "--engine", engine, "-o", str(Path(temp) / "out")])
                self.assertNotIn("engine must be", result.output)

    def test_convert_accepts_the_model_free_pdf_engine(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "notes.md"
            source.write_text("# Title\n", encoding="utf-8")
            result = self.runner.invoke(
                app, ["convert", str(source), "--engine", "docling-native", "-o", str(Path(temp) / "out")]
            )
        # The engine name is accepted (no usage error, exit 2); converting Markdown
        # with a PDF-only engine then fails that file, so the command exits 1.
        self.assertEqual(result.exit_code, 1)
        self.assertNotIn("engine must be", result.output)

    def test_a_scan_with_no_text_names_the_ocr_engines_to_install(self):
        from document_converter.models import ConversionResult, no_text_recovered_message
        message = no_text_recovered_message(ConversionResult(source=Path("scan.pdf"), engine="docling-native", markdown=""))
        for name in ("Marker", "MinerU", "document-converter list-engines"):
            self.assertIn(name, message)

    def test_convert_rejects_an_unknown_engine(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "notes.md"
            source.write_text("# Title\n", encoding="utf-8")
            result = self.runner.invoke(app, ["convert", str(source), "--engine", "nope"])
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("docling-native", result.output)

    def test_convert_exits_non_zero_when_a_file_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            good = Path(temp) / "in" / "good.md"
            good.parent.mkdir()
            good.write_text("# Fine\n", encoding="utf-8")
            (good.parent / "bad.md").write_text("# Broken\n", encoding="utf-8")
            original = __import__("document_converter.pipeline", fromlist=["convert_one"]).convert_one

            def fail_on_bad(path, *args, **kwargs):
                if path.name == "bad.md":
                    raise RuntimeError("boom")
                return original(path, *args, **kwargs)

            with patch("document_converter.pipeline.convert_one", side_effect=fail_on_bad):
                result = self.runner.invoke(
                    app, ["convert", str(good.parent), "--engine", "text_direct", "-o", str(Path(temp) / "out")]
                )
        self.assertEqual(result.exit_code, 1)
        self.assertIn("FAILED", result.output)

    def test_list_engines_does_not_count_docling_slim_alone_as_a_pdf_reader(self):
        # Bare docling-slim provides the docling namespace but not docling-parse,
        # the PDF parser, nor docling-ibm-models, the full pipeline's layout models.
        present = {"docling", "docling.document_converter", "docling.pipeline.native_pdf_pipeline"}
        with patch("document_converter.cli._importable", side_effect=lambda name: name in present):
            result = self.runner.invoke(app, ["list-engines"])
        lines = {line.split()[0]: line for line in result.output.splitlines() if line.strip()}
        self.assertIn("not detected", lines["docling"])
        self.assertIn("not detected", lines["docling-native"])

    def test_list_engines_detects_the_pdf_readers_when_their_parts_are_installed(self):
        present = {
            "docling", "docling.document_converter", "docling.pipeline.native_pdf_pipeline",
            "docling_parse", "docling_ibm_models",
        }
        with patch("document_converter.cli._importable", side_effect=lambda name: name in present):
            result = self.runner.invoke(app, ["list-engines"])
        lines = {line.split()[0]: line for line in result.output.splitlines() if line.strip()}
        self.assertNotIn("not detected", lines["docling"])
        self.assertNotIn("not detected", lines["docling-native"])
        self.assertIn("format-pdf", lines["docling-native"])

if __name__ == "__main__":
    unittest.main()
