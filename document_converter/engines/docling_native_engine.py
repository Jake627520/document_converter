"""Model-free PDF adapter built on Docling's native PDF pipeline.

The default Docling pipeline runs layout and table models, which require PyTorch
and model weights downloaded on first use. This adapter selects Docling's
``NativePdfPipeline`` instead: it reads the text cells and bitmaps the PDF
already contains and runs no models, so it works from a plain
``pip install docling-slim`` with no network access and no GPU stack. The cost is
structure - there is no heading hierarchy, no Markdown table reconstruction, no
reading-order recovery and no OCR, so a scanned PDF yields no text.
"""
import sys
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

def _format_options(NativePdfPipelineOptions) -> dict:
    """Pipeline and backend options; on Windows, without page images.

    Docling's threaded parser renders a picture of every page while decoding it,
    and the native pipeline stores that picture in the Docling JSON. On Windows
    the renderer corrupts the heap when its worker threads exit (docling-parse
    issue #357, open as of 7.25.0): access violations, then a crash in unrelated
    code after any number of documents. There, pages are not rendered, so the
    Docling JSON carries no page images; the text, Markdown and HTML are the
    same. Elsewhere the renderer is sound and the output is left as it was. A
    Docling without the threaded backend renders nothing it could turn off.
    """
    if sys.platform != "win32":
        return {"pipeline_options": NativePdfPipelineOptions()}
    try:
        from docling.datamodel.backend_options import ThreadedDoclingParseBackendOptions
    except ImportError:
        return {"pipeline_options": NativePdfPipelineOptions()}
    return {
        "pipeline_options": NativePdfPipelineOptions(generate_page_images=False),
        "backend_options": ThreadedDoclingParseBackendOptions(render_pages=False),
    }


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
                        **_format_options(NativePdfPipelineOptions),
                    )
                }
            )
            conversion = converter.convert(str(path))
            result = build_result(conversion.document, path, self.name, image_mode)
        except Exception as e:
            raise EngineError(f"docling-native failed for {path}: {e}") from e

        result.warnings.append(QUALITY_WARNING)
        if not result.has_recovered_text():
            result.warnings.append(NO_TEXT_WARNING)
        return result
