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
from document_converter.engines.docling_native_engine import DoclingNativePdfEngine


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

    def test_html_entities_from_the_markdown_serializer_are_undone(self):
        """Docling escapes the document's own text when it serializes Markdown.

        The document model holds that text unescaped, so the entities belong to
        the serializer, not to the document, and neither Markdown nor plain text
        may carry them: a spec sheet reading "Inbound & Outbound" must not be
        written out as "Inbound &amp; Outbound".
        """
        document = SimpleNamespace(
            export_to_markdown=lambda: '## A &amp; B\n\n5 &lt; 6 &gt; 4, said &quot;hi&quot;\n',
            export_to_dict=lambda: {"text": 'A & B, 5 < 6, said "hi"'},
        )
        result = self.convert_with_document(document)
        self.assertEqual(result.markdown, '## A & B\n\n5 < 6 > 4, said "hi"\n')
        self.assertEqual(result.text, 'A & B\n\n5 < 6 > 4, said "hi"\n')

    def test_exactly_one_level_is_undone_so_a_written_out_entity_survives(self):
        """A document whose own text reads "&amp;" is exported doubly escaped."""
        document = SimpleNamespace(
            export_to_markdown=lambda: "write &amp;amp; for an ampersand\n",
            export_to_dict=lambda: {},
        )
        result = self.convert_with_document(document)
        self.assertEqual(result.markdown, "write &amp; for an ampersand\n")

    def test_engine_html_keeps_the_entities_that_belong_there(self):
        document = SimpleNamespace(
            export_to_markdown=lambda: "A &amp; B\n",
            export_to_html=lambda: "<p>A &amp; B</p>",
            export_to_dict=lambda: {},
        )
        result = self.convert_with_document(document)
        self.assertEqual(result.markdown, "A & B\n")
        self.assertEqual(result.html, "<p>A &amp; B</p>")

    def test_serialization_failure_retains_cause_and_source_in_engine_error(self):
        failure = ValueError("invalid document representation")
        document = SimpleNamespace(export_to_markdown=Mock(side_effect=failure))
        with self.assertRaisesRegex(EngineError, "Docling failed for paper.pdf") as caught:
            self.convert_with_document(document)
        self.assertIs(caught.exception.__cause__, failure)


class DoclingNativePdfAdapterTests(unittest.TestCase):
    """The model-free PDF adapter must not need PyTorch or downloaded weights."""

    def convert_with_document(self, document, source=Path("paper.pdf")):
        converter = Mock()
        converter.convert.return_value = SimpleNamespace(document=document)
        modules = {
            "docling": SimpleNamespace(),
            "docling.datamodel": SimpleNamespace(),
            "docling.datamodel.base_models": SimpleNamespace(InputFormat=SimpleNamespace(PDF="pdf")),
            "docling.datamodel.pipeline_options": SimpleNamespace(NativePdfPipelineOptions=Mock()),
            "docling.document_converter": SimpleNamespace(
                DocumentConverter=Mock(return_value=converter), PdfFormatOption=Mock()
            ),
            "docling.pipeline": SimpleNamespace(),
            "docling.pipeline.native_pdf_pipeline": SimpleNamespace(NativePdfPipeline=object),
        }
        with patch.dict(sys.modules, modules):
            result = DoclingNativePdfEngine().convert(source, "none")
        converter.convert.assert_called_once_with(str(source))
        return result

    def test_only_pdf_input_is_accepted(self):
        engine = DoclingNativePdfEngine()
        self.assertTrue(engine.can_handle(Path("paper.PDF")))
        self.assertFalse(engine.can_handle(Path("scan.png")))
        self.assertFalse(engine.can_handle(Path("notes.md")))
        with self.assertRaisesRegex(EngineError, "only converts PDF"):
            engine.convert(Path("notes.md"), "none")

    def test_missing_native_pipeline_is_reported_as_an_engine_error(self):
        with patch.dict(sys.modules, {"docling.pipeline.native_pdf_pipeline": None}):
            with self.assertRaisesRegex(EngineError, "native PDF pipeline is unavailable"):
                DoclingNativePdfEngine().convert(Path("paper.pdf"), "none")

    def test_conversion_reports_the_engine_and_its_quality_limits(self):
        document = SimpleNamespace(
            export_to_markdown=lambda: "規格表\n\n84\n",
            export_to_dict=lambda: {"name": "paper"},
        )
        result = self.convert_with_document(document)
        self.assertEqual(result.engine, "docling-native")
        self.assertEqual(result.markdown, "規格表\n\n84\n")
        self.assertEqual(json.loads(result.json_text), {"name": "paper"})
        self.assertTrue(any("no layout, table or OCR model" in w for w in result.warnings))

    def test_empty_output_warns_that_no_ocr_ran(self):
        document = SimpleNamespace(export_to_markdown=lambda: "<!-- image -->", export_to_dict=lambda: {})
        result = self.convert_with_document(document, Path("scan.pdf"))
        self.assertTrue(any("runs no OCR" in w for w in result.warnings))

    def test_conversion_failure_retains_cause_and_source(self):
        failure = ValueError("broken page tree")
        document = SimpleNamespace(export_to_markdown=Mock(side_effect=failure))
        with self.assertRaisesRegex(EngineError, "docling-native failed for paper.pdf") as caught:
            self.convert_with_document(document)
        self.assertIs(caught.exception.__cause__, failure)


if __name__ == "__main__":
    unittest.main()
