from pathlib import Path
import typer
from rich.console import Console
from rich.table import Table
from .pipeline import discover_inputs, process_batch, DEFAULT_PARALLEL, MAX_WORKER_LIMIT
from .detector import inspect_pdf
from .watcher import watch_directory, validate_watch_paths, validate_watch_interval

app = typer.Typer(add_completion=False, no_args_is_help=True)
console = Console()

@app.command()
def convert(
    source: Path = typer.Argument(..., exists=True, readable=True),
    to: list[str] = typer.Option(["md"], "--to", help="Outputs: md html json txt. Repeat --to."),
    output: Path = typer.Option(Path("./converted"), "--output", "-o"),
    engine: str = typer.Option("auto", "--engine", help="auto, docling, docling-native, marker, mineru"),
    images: str = typer.Option("none", "--images", help="none, referenced, embedded"),
    clean: bool = typer.Option(False, "--clean", help="Clean up markdown formatting and page artifacts"),
    strip_page_numbers: bool = typer.Option(
        False,
        "--strip-page-numbers",
        help="With --clean, also drop lines holding only digits. Off by default because those lines "
             "are often table values rather than page numbers.",
    ),
    preserve_layout: bool = typer.Option(False, "--preserve-layout", help="Preserve raw page breaks and layout in markdown"),
    parallel: int = typer.Option(
        DEFAULT_PARALLEL,
        "--parallel",
        "-p",
        help=(
            f"Concurrent workers for batch conversion (1-{MAX_WORKER_LIMIT}; default {DEFAULT_PARALLEL}). "
            "Helps when converting many files; a single large PDF gains little because conversion is "
            "engine-bound (and under the GIL for in-process engines)."
        ),
    ),
    watch: bool = typer.Option(False, "--watch", help="Watch a directory for new or changed files"),
    watch_interval: float = typer.Option(1.0, "--watch-interval", help="Finite polling interval in seconds when --watch is enabled"),
):
    """Convert local documents to Markdown/HTML/JSON/text."""
    valid = {"md", "html", "json", "txt"}
    bad = set(to) - valid
    if bad:
        raise typer.BadParameter(f"Unsupported output(s): {', '.join(sorted(bad))}")
    if engine not in {"auto", "text_direct", "docling", "docling-native", "marker", "mineru"}:
        raise typer.BadParameter("engine must be auto, text_direct, docling, docling-native, marker, or mineru")
    if images not in {"none", "referenced", "embedded"}:
        raise typer.BadParameter("images must be none, referenced, or embedded")
    if parallel < 1:
        raise typer.BadParameter("--parallel must be at least 1")
    if parallel > MAX_WORKER_LIMIT:
        raise typer.BadParameter(f"--parallel cannot exceed the safe limit of {MAX_WORKER_LIMIT}")
    if watch:
        try:
            validate_watch_interval(watch, watch_interval)
            validate_watch_paths(source, output)
        except ValueError as exc:
            raise typer.BadParameter(str(exc)) from exc

        def report_watch_results(batch_results):
            for item in batch_results:
                if item["success"]:
                    console.print(f"[green]converted[/green] {item['path']}")
                    for warning in item.get("warnings", []):
                        console.print(f"[yellow]warning:[/yellow] {item['path']}: {warning}")
                else:
                    console.print(f"[red]failed[/red] {item['path']}: {item.get('error')}")

        try:
            watch_directory(
                source,
                output,
                interval=watch_interval,
                formats=to,
                engine_name=engine,
                image_mode=images,
                clean=clean,
                preserve_layout=preserve_layout,
                parallel=parallel,
                strip_bare_numbers=strip_page_numbers,
                on_results=report_watch_results,
            )
        except KeyboardInterrupt:
            console.print("Watch stopped.")
        return

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
        strip_bare_numbers=strip_page_numbers,
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
    table = Table()
    table.add_column("File", overflow="fold")
    table.add_column("Pages")
    table.add_column("Chars")
    table.add_column("Layer")
    table.add_column("Type")
    table.add_column("Tool")
    source_root = source if source.is_dir() else source.parent
    for path in inputs:
        display_path = path.relative_to(source_root).as_posix() if source.is_dir() else path.name
        if path.suffix.lower() == ".pdf":
            try:
                prof = inspect_pdf(path)
                table.add_row(
                    display_path,
                    str(prof.page_count),
                    str(prof.total_chars),
                    "Yes" if prof.has_text_layer else "No",
                    prof.classification,
                    prof.details.get("analyzer", "default"),
                )
            except Exception as e:
                table.add_row(display_path, "-", "-", "-", f"ERROR: {e}", "-")
        else:
            table.add_row(display_path, "-", "-", "-", "non-pdf", "-")
    console.print(table)

@app.command("list-engines")
def list_engines():
    """Show available engines."""
    import shutil
    rows = [
        ("text_direct", "built-in (always available)", "UTF-8 Markdown / plain text"),
        ("docling", "pip install docling", "primary/local"),
        ("docling-native", "pip install docling-slim", "model-free PDF text reader"),
        ("marker", "pip install marker-pdf", "optional PDF fallback"),
        ("mineru", "pip install 'mineru>=4,<5'", "optional PDF/OCR fallback"),
    ]
    for name, install, role in rows:
        if name == "text_direct":
            found = "installed"
        else:
            found = "installed" if (
                (name == "docling" and _importable("docling")) or
                (name == "docling-native" and _importable("docling.pipeline.native_pdf_pipeline")) or
                (name == "marker" and shutil.which("marker_single")) or
                (name == "mineru" and shutil.which("mineru-kit"))
            ) else "not detected"
        # soft_wrap: an install command broken across lines reads as two commands.
        console.print(f"{name:14} {found:12} {role:26} {install}", soft_wrap=True)

@app.command("web")
def web(
    port: int = typer.Option(8765, "--port", min=1024, max=65535, help="Local browser port (server binds only to 127.0.0.1)"),
):
    """Start the local browser workbench at http://127.0.0.1:<port>."""
    try:
        import uvicorn
    except ImportError as exc:
        raise typer.BadParameter('Install the web extra first: pip install -e ".[web]"') from exc
    uvicorn.run("document_converter.web_app:app", host="127.0.0.1", port=port, reload=False, access_log=False)

def _importable(name: str) -> bool:
    try:
        __import__(name)
        return True
    except Exception:
        return False

if __name__ == "__main__":
    app()
