"""Model-free PDF adapter built on Docling's native PDF pipeline.

The default Docling pipeline runs layout and table models, which require PyTorch
and model weights downloaded on first use. This adapter selects Docling's
``NativePdfPipeline`` instead: it reads the text cells and bitmaps the PDF
already contains and runs no models, so it works from a plain
``pip install docling-slim`` with no network access and no GPU stack. The cost is
structure - there is no heading hierarchy, no Markdown table reconstruction, no
reading-order recovery and no OCR, so a scanned PDF yields no text.
"""
import re
from pathlib import Path
from .base import Engine, EngineError
from .docling_engine import build_result
from ..models import ConversionResult, ImageMode

QUALITY_WARNING = (
    "docling-native ran no layout, table or OCR model: text and images are extracted as the PDF "
    "stores them, without heading levels, Markdown tables or reading-order recovery."
)

NO_TEXT_WARNING = (
    "No text was recovered. The PDF has no text layer and this engine runs no OCR; "
    "use an engine with OCR support for scanned pages."
)

_PLACEHOLDER = re.compile(r"<!--.*?-->", re.DOTALL)


def _has_recovered_text(markdown: str | None) -> bool:
    """A page of image placeholders is not recovered text."""
    return bool(_PLACEHOLDER.sub("", markdown or "").strip())


class DoclingNativePdfEngine(Engine):
    name = "docling-native"

    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() == ".pdf"

    def convert(self, path: Path, image_mode: ImageMode) -> ConversionResult:
        if not self.can_handle(path):
            raise EngineError(f"docling-native only converts PDF input, not {path.suffix or 'unknown'}")
        try:
            from docling.datamodel.base_models import InputFormat
            from docling.datamodel.pipeline_options import NativePdfPipelineOptions
            from docling.document_converter import DocumentConverter, PdfFormatOption
            from docling.pipeline.native_pdf_pipeline import NativePdfPipeline
        except Exception as e:
            raise EngineError(f"Docling's native PDF pipeline is unavailable: {e}") from e

        try:
            converter = DocumentConverter(
                format_options={
                    InputFormat.PDF: PdfFormatOption(
                        pipeline_cls=NativePdfPipeline,
                        pipeline_options=NativePdfPipelineOptions(),
                    )
                }
            )
            conversion = converter.convert(str(path))
            result = build_result(conversion.document, path, self.name, image_mode)
        except Exception as e:
            raise EngineError(f"docling-native failed for {path}: {e}") from e

        result.warnings.append(QUALITY_WARNING)
        if not _has_recovered_text(result.markdown):
            result.warnings.append(NO_TEXT_WARNING)
        return result
