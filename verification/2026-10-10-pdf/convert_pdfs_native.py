"""Convert PDFs with Docling's model-free pipeline, bypassing the engine registry.

This harness found the model-free route before the CLI exposed it. For ordinary
use prefer the shipped command, which now does the same thing:

    document-converter convert ~/Documents/pdfs --engine docling-native --to md --to html

The script is kept for the one thing the CLI cannot do: with
``--project-html-output`` it drops Docling's own HTML so ``writer.py`` falls back
to this project's ``renderer.render_html``, which is how the HTML files in
``results-project-renderer/`` were produced.

Usage (from the repository root, in a virtualenv that has docling-slim):

    python verification/2026-10-10-pdf/convert_pdfs_native.py
    python verification/2026-10-10-pdf/convert_pdfs_native.py --input ~/Documents/pdfs --output ~/Desktop/converted
"""
import argparse
import json
import sys
import time
from dataclasses import replace
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import NativePdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.pipeline.native_pdf_pipeline import NativePdfPipeline

from document_converter.detector import inspect_pdf
from document_converter.engines.docling_engine import _markdown_to_text
from document_converter.models import ConversionResult
from document_converter.writer import write_result

FORMATS = ["md", "html", "json", "txt"]


def build_converter() -> DocumentConverter:
    return DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_cls=NativePdfPipeline,
                pipeline_options=NativePdfPipelineOptions(),
            )
        }
    )


def discover(source: Path) -> list[Path]:
    if source.is_file():
        return [source]
    return sorted(source.rglob("*.pdf"))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", type=Path, default=HERE / "samples", help="PDF file or directory of PDFs")
    parser.add_argument("--output", type=Path, default=HERE / "results-clean", help="output directory")
    parser.add_argument(
        "--raw-output",
        type=Path,
        default=None,
        help="optional second output directory written without --clean, for comparison",
    )
    parser.add_argument(
        "--project-html-output",
        type=Path,
        default=None,
        help="optional directory written with Docling's HTML dropped, so writer.py falls back to this "
             "project's own renderer.render_html",
    )
    parser.add_argument("--report", type=Path, default=None, help="where to write the JSON run summary")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not args.input.exists():
        print(f"input not found: {args.input}", file=sys.stderr)
        return 2

    converter = build_converter()
    summary = []
    for pdf in discover(args.input):
        profile = inspect_pdf(pdf)
        started = time.perf_counter()
        record = {
            "file": pdf.name,
            "pages": profile.page_count,
            "detector_classification": profile.classification,
            "detector_chars": profile.total_chars,
        }
        try:
            conv = converter.convert(str(pdf))
            doc = conv.document
            markdown = doc.export_to_markdown()
            result = ConversionResult(
                source=pdf,
                engine="docling-native-pdf",
                markdown=markdown,
                html=doc.export_to_html(),
                json_text=json.dumps(doc.export_to_dict(), ensure_ascii=False, indent=2),
                text=_markdown_to_text(markdown),
            )
            targets = [(args.output, True)]
            if args.raw_output is not None:
                targets.append((args.raw_output, False))
            for output_dir, clean in targets:
                write_result(result=result, output_dir=output_dir, formats=FORMATS, clean=clean)
            if args.project_html_output is not None:
                write_result(
                    result=replace(result, html=None),
                    output_dir=args.project_html_output,
                    formats=["html"],
                    clean=True,
                )
            record.update(
                status=str(conv.status).split(".")[-1],
                markdown_chars=len(markdown),
                outputs=[f"{pdf.stem}.{fmt}" for fmt in FORMATS],
            )
            if record["markdown_chars"] < 32:
                record["note"] = "almost no text recovered; the PDF has no text layer and this pipeline runs no OCR"
        except Exception as exc:  # noqa: BLE001 - report per file instead of aborting the batch
            record.update(status="FAILED", error=f"{type(exc).__name__}: {exc}")
        record["seconds"] = round(time.perf_counter() - started, 2)
        summary.append(record)
        print(json.dumps(record, ensure_ascii=False))

    if not summary:
        print(f"no PDF found under {args.input}", file=sys.stderr)
        return 2

    report = args.report or (HERE / "reports" / "native-pdf-summary.json")
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0 if all(record["status"] == "SUCCESS" for record in summary) else 1


if __name__ == "__main__":
    raise SystemExit(main())
