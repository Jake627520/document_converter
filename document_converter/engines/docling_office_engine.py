"""Model-free Office adapter: Word, PowerPoint and Excel through Docling.

Docling reads .docx, .pptx and .xlsx with python-docx, python-pptx and openpyxl
and builds its document from what the file declares - headings, lists, tables -
without a layout model, OCR or PyTorch. Docling's default converter would do
the same for these formats; this adapter restricts the converter to them, so it
can never fall through to a pipeline that wants model weights. It works from a
plain ``pip install "docling-slim[convert-core,format-office]"``.

Pictures inside a document are kept as pictures; their text is not read.
"""
from pathlib import Path
from .base import Engine, EngineError
from .docling_engine import build_result
from ..models import ConversionResult, ImageMode

OFFICE_SUFFIXES = frozenset({".docx", ".pptx", ".xlsx"})


class DoclingOfficeEngine(Engine):
    name = "docling-office"

    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() in OFFICE_SUFFIXES

    def convert(self, path: Path, image_mode: ImageMode) -> ConversionResult:
        if not self.can_handle(path):
            raise EngineError(
                f"docling-office only converts .docx, .pptx and .xlsx, not {path.suffix or 'unknown'}"
            )
        try:
            from docling.datamodel.base_models import InputFormat
            from docling.document_converter import DocumentConverter
        except Exception as e:
            raise EngineError(f"Docling's Office reader is unavailable: {e}") from e

        try:
            converter = DocumentConverter(
                allowed_formats=[InputFormat.DOCX, InputFormat.PPTX, InputFormat.XLSX]
            )
            conversion = converter.convert(str(path))
            return build_result(conversion.document, path, self.name, image_mode)
        except Exception as e:
            raise EngineError(f"docling-office failed for {path}: {e}") from e
