from pathlib import Path
import typer
from rich.console import Console
from rich.table import Table
from .pipeline import discover_inputs, process_batch, DEFAULT_PARALLEL, MAX_WORKER_LIMIT
from .detector import inspect_pdf

app = typer.Typer(add_completion=False, no_args_is_help=True)
console = Console()

@app.command()
def convert(
    source: Path = typer.Argument(..., exists=True, readable=True),
    to: list[str] = typer.Option(["md"], "--to", help="Outputs: md html json txt. Repeat --to."),
    output: Path = typer.Option(Path("./converted"), "--output", "-o"),
    engine: str = typer.Option("auto", "--engine", help="auto, docling, marker, mineru"),
    images: str = typer.Option("none", "--images", help="none, referenced, embedded"),
    clean: bool = typer.Option(False, "--clean", help="Clean up markdown formatting and page artifacts"),
    preserve_layout: bool = typer.Option(False, "--preserve-layout", help="Preserve raw page breaks and layout in markdown"),
    parallel: int = typer.Option(DEFAULT_PARALLEL, "--parallel", "-p", help=f"Concurrent worker count (1-{MAX_WORKER_LIMIT})"),
):
    """Convert local documents to Markdown/HTML/JSON/text."""
    valid = {"md", "html", "json", "txt"}
    bad = set(to) - valid
    if bad:
        raise typer.BadParameter(f"Unsupported output(s): {', '.join(sorted(bad))}")
    if engine not in {"auto", "docling", "marker", "mineru"}:
        raise typer.BadParameter("engine must be auto, docling, marker, or mineru")
    if images not in {"none", "referenced", "embedded"}:
        raise typer.BadParameter("images must be none, referenced, or embedded")
    if parallel < 1:
        raise typer.BadParameter("--parallel must be at least 1")
    if parallel > MAX_WORKER_LIMIT:
        raise typer.BadParameter(f"--parallel cannot exceed the safe limit of {MAX_WORKER_LIMIT}")

    inputs = discover_inputs(source)
    batch_results = process_batch(
        inputs=inputs,
        output_dir=output,
        formats=to,
        engine_name=engine,
        image_mode=images,
        clean=clean,
        preserve_layout=preserve_layout,
        parallel=parallel,
        source_root=source,
    )

    table = Table("Source", "Engine", "Type", "Outputs", "Status")
    for item in batch_results:
        path = item["path"]
        if item["success"]:
            profile = item.get("metadata", {}).get("pdf_profile")
            doc_type = profile.classification if profile else path.suffix.lower()
            status = "OK"
            if item.get("warnings"):
                status = "OK (warnings)"
            table.add_row(str(path), item.get("engine", "-"), doc_type, ", ".join(to), status)
            for warning in item.get("warnings", []):
                console.print(f"[yellow]warning:[/yellow] {path}: {warning}")
        else:
            table.add_row(str(path), "-", path.suffix.lower(), ", ".join(to), f"FAILED: {item.get('error')}")

    console.print(table)

@app.command("inspect")
def inspect_cmd(
    source: Path = typer.Argument(..., exists=True, readable=True),
):
    """Inspect whether a PDF has text layers or is scanned/image-based."""
    inputs = discover_inputs(source)
    table = Table("File", "Pages", "Text Chars", "Text Layer", "Classification", "Analyzer")
    for path in inputs:
        if path.suffix.lower() == ".pdf":
            try:
                prof = inspect_pdf(path)
                table.add_row(
                    str(path),
                    str(prof.page_count),
                    str(prof.total_chars),
                    "Yes" if prof.has_text_layer else "No",
                    prof.classification,
                    prof.details.get("analyzer", "default"),
                )
            except Exception as e:
                table.add_row(str(path), "-", "-", "-", f"ERROR: {e}", "-")
        else:
            table.add_row(str(path), "-", "-", "-", "non-pdf", "-")
    console.print(table)

@app.command("list-engines")
def list_engines():
    """Show available engines."""
    import shutil
    rows = [
        ("docling", "pip install docling", "primary/local"),
        ("marker", "pip install marker-pdf", "optional PDF fallback"),
        ("mineru", "install local MinerU 4.x", "optional PDF/OCR fallback"),
    ]
    for name, install, role in rows:
        found = "installed" if (
            (name == "docling" and _importable("docling")) or
            (name == "marker" and shutil.which("marker_single")) or
            (name == "mineru" and (shutil.which("mineru") or shutil.which("mineru-kit")))
        ) else "not detected"
        console.print(f"{name:8} {found:12} {role:24} {install}")

def _importable(name: str) -> bool:
    try:
        __import__(name)
        return True
    except Exception:
        return False

if __name__ == "__main__":
    app()
