"""Tests verifying core functionality works without requiring docling installed."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner
from document_converter.cli import app
from document_converter.pipeline import convert_one, choose_engine
from document_converter.engines.text_direct_engine import TextDirectEngine
from document_converter.engines.base import EngineError


class OptionalDependenciesTests(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()

    def test_core_install_does_not_require_docling_import(self):
        """Without docling imported, text conversion and CLI list-engines work cleanly."""
        with tempfile.TemporaryDirectory() as temp:
            md_path = Path(temp) / "sample.md"
            md_path.write_text("# Core Markdown\n\nTesting minimal install.\n", encoding="utf-8")

            # 1. TextDirectEngine works directly
            engine = TextDirectEngine()
            self.assertTrue(engine.can_handle(md_path))
            res = engine.convert(md_path, "none")
            self.assertEqual(res.engine, "text_direct")
            self.assertIn("Core Markdown", res.markdown)

            # 2. convert_one with auto engine succeeds for markdown without touching docling
            res_auto = convert_one(md_path, "auto", "none")
            self.assertEqual(res_auto.engine, "text_direct")
            self.assertIn("Core Markdown", res_auto.markdown)

            # 3. list-engines shows text_direct installed
            result = self.runner.invoke(app, ["list-engines"])
            self.assertEqual(result.exit_code, 0)
            self.assertIn("text_direct", result.output)
            self.assertIn("installed", result.output)

    def test_list_engines_reports_not_detected_when_docling_not_installed(self):
        """list-engines allows docling to be not detected."""
        def mock_importable(name: str) -> bool:
            if "docling" in name:
                return False
            return True

        with patch("document_converter.cli._importable", side_effect=mock_importable):
            result = self.runner.invoke(app, ["list-engines"])
            self.assertEqual(result.exit_code, 0)
            self.assertIn("text_direct", result.output)
            self.assertIn("installed", result.output)
            self.assertIn("docling", result.output)
            self.assertIn("not detected", result.output)

    def test_convert_pdf_gives_engine_unavailable_error_when_docling_missing(self):
        """Converting a PDF when docling fails reports engine failure, not install crash."""
        class MockFailingDocling:
            name = "docling"
            def can_handle(self, p): return True
            def convert(self, p, mode):
                raise EngineError("docling is unavailable in minimal install")

        with tempfile.TemporaryDirectory() as temp:
            pdf_path = Path(temp) / "test.pdf"
            pdf_path.write_bytes(b"%PDF-1.4\n")

            with patch("document_converter.pipeline.choose_engine", return_value=[MockFailingDocling()]):
                result = self.runner.invoke(app, ["convert", str(pdf_path), "--to", "md", "-o", str(Path(temp) / "out")])
                self.assertIn("FAILED", result.output)
                self.assertIn("unavailable", result.output)
                self.assertIn("docling", result.output)


if __name__ == "__main__":
    unittest.main()
