"""Adapter contracts using local stubs; no optional engines or models are loaded."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from document_converter.engines.base import EngineError
from document_converter.engines.command_engine import MarkerEngine, MinerUEngine
from document_converter.engines.docling_engine import DoclingEngine


class CommandAdapterTests(unittest.TestCase):
    def test_missing_optional_executable_fails_before_starting_process(self):
        with patch("document_converter.engines.command_engine.shutil.which", return_value=None), patch(
            "document_converter.engines.command_engine.subprocess.run"
        ) as run:
            for engine in (MarkerEngine(), MinerUEngine()):
                with self.subTest(engine=engine.name), self.assertRaisesRegex(EngineError, "CLI not found"):
                    engine.convert(Path("missing.pdf"), "none")
            run.assert_not_called()

    def test_input_capabilities_match_document_types(self):
        self.assertTrue(MarkerEngine().can_handle(Path("paper.PDF")))
        self.assertFalse(MarkerEngine().can_handle(Path("notes.txt")))
        self.assertTrue(MinerUEngine().can_handle(Path("scan.PNG")))
        self.assertFalse(MinerUEngine().can_handle(Path("notes.md")))

    def test_shell_metacharacters_remain_one_argument_and_output_is_read(self):
        for engine in (MarkerEngine(), MinerUEngine()):
            with self.subTest(engine=engine.name), tempfile.TemporaryDirectory() as tmp:
                source = Path(tmp) / "paper ; $(touch unwanted).pdf"
                source.write_bytes(b"synthetic input")

                def invoke(argv, **kwargs):
                    self.assertIsInstance(argv, list)
                    self.assertIn(str(source), argv)
                    self.assertFalse(kwargs.get("shell", False))
                    self.assertTrue(kwargs["check"])
                    if engine.name == "marker":
                        output = Path(argv[argv.index("--output_dir") + 1]) / "paper.md"
                    else:
                        output = Path(argv[argv.index("-o") + 1])
                    output.write_text("# Converted\n\n本機內容\n", encoding="utf-8")
                    return subprocess.CompletedProcess(argv, 0)

                with patch("document_converter.engines.command_engine.shutil.which", return_value="/stub/engine"), patch(
                    "document_converter.engines.command_engine.subprocess.run", side_effect=invoke
                ) as run:
                    result = engine.convert(source, "none")
                run.assert_called_once()
                self.assertEqual(result.source, source)
                self.assertEqual(result.engine, engine.name)
                self.assertEqual(result.markdown, "# Converted\n\n本機內容\n")
                self.assertEqual(result.text, result.markdown)
                self.assertIsNone(result.html)
                self.assertTrue(result.warnings)
                self.assertFalse((Path(tmp) / "unwanted").exists())

    def test_failed_cli_reports_stderr_as_engine_error(self):
        failure = subprocess.CalledProcessError(2, ["stub"], stderr="cannot parse document")
        with tempfile.TemporaryDirectory() as tmp, patch(
            "document_converter.engines.command_engine.shutil.which", return_value="/stub/engine"
        ), patch("document_converter.engines.command_engine.subprocess.run", side_effect=failure):
            for engine in (MarkerEngine(), MinerUEngine()):
                with self.subTest(engine=engine.name), self.assertRaisesRegex(EngineError, "cannot parse document"):
                    engine.convert(Path(tmp) / "paper.pdf", "none")

    def test_successful_cli_without_output_is_not_a_successful_conversion(self):
        with tempfile.TemporaryDirectory() as tmp, patch(
            "document_converter.engines.command_engine.shutil.which",
            side_effect=lambda name: None if name == "mineru-kit" else "/stub/engine",
        ), patch("document_converter.engines.command_engine.subprocess.run"):
            for engine in (MarkerEngine(), MinerUEngine()):
                with self.subTest(engine=engine.name), self.assertRaisesRegex(EngineError, "Markdown output"):
                    engine.convert(Path(tmp) / "paper.pdf", "none")


class DoclingAdapterTests(unittest.TestCase):
    def convert_with_document(self, document, mode="none"):
        converter = Mock()
        converter.convert.return_value = SimpleNamespace(document=document)
        factory = Mock(return_value=converter)
        module = SimpleNamespace(DocumentConverter=factory)
        with patch.dict(sys.modules, {"docling": SimpleNamespace(), "docling.document_converter": module}):
            result = DoclingEngine().convert(Path("paper.pdf"), mode)
        converter.convert.assert_called_once_with("paper.pdf")
        return result

    def test_missing_docling_is_reported_without_loading_an_engine(self):
        with patch.dict(sys.modules, {"docling": None, "docling.document_converter": None}):
            with self.assertRaisesRegex(EngineError, "Docling is not installed"):
                DoclingEngine().convert(Path("paper.pdf"), "none")

    def test_document_serialization_preserves_unicode_and_plain_text(self):
        document = SimpleNamespace(
            export_to_markdown=lambda: "## Title\n\n- 項目\n```python\nprint(1)\n```\n",
            export_to_dict=lambda: {"title": "本機文件"},
        )
        result = self.convert_with_document(document)
        self.assertEqual(json.loads(result.json_text), {"title": "本機文件"})
        self.assertEqual(result.text, "Title\n\n項目\nprint(1)\n")
        self.assertEqual(result.assets, {})
        self.assertIsNone(result.html)
        self.assertEqual(result.engine, "docling")

    def test_referenced_assets_from_both_serializers_are_preserved(self):
        document = SimpleNamespace(
            export_to_markdown_with_images=lambda mode, directory: (
                "![image](assets/md.png)", [(Path("assets/md.png"), b"markdown image")]
            ),
            export_to_html_with_images=lambda mode, directory: (
                '<img src="assets/html.png">', [(Path("assets/html.png"), b"html image")]
            ),
            export_to_dict=lambda: {},
        )
        result = self.convert_with_document(document, "referenced")
        self.assertEqual(result.assets, {"assets/md.png": b"markdown image", "assets/html.png": b"html image"})
        self.assertEqual(result.html, '<img src="assets/html.png">')

    def test_serialization_failure_retains_cause_and_source_in_engine_error(self):
        failure = ValueError("invalid document representation")
        document = SimpleNamespace(export_to_markdown=Mock(side_effect=failure))
        with self.assertRaisesRegex(EngineError, "Docling failed for paper.pdf") as caught:
            self.convert_with_document(document)
        self.assertIs(caught.exception.__cause__, failure)


if __name__ == "__main__":
    unittest.main()
