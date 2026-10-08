from pathlib import Path
import typer
from rich.console import Console
from rich.table import Table
from .pipeline import discover_inputs, convert_one
from .writer import write_result

app = typer.Typer(add_completion=False, no_args_is_help=True)
console = Console()

@app.command()
def convert(
    source: Path = typer.Argument(..., exists=True, readable=True),
    to: list[str] = typer.Option(["md"], "--to", help="Outputs: md html json txt. Repeat --to."),
    output: Path = typer.Option(Path("./converted"), "--output", "-o"),
    engine: str = typer.Option("auto", "--engine", help="auto, docling, marker, mineru"),
    images: str = typer.Option("none", "--images", help="none, referenced, embedded"),
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

    inputs = discover_inputs(source)
    table = Table("Source", "Engine", "Outputs", "Status")
    for path in inputs:
        # Preserve directory structure for batch jobs.
        rel_parent = path.parent.relative_to(source) if source.is_dir() else Path(".")
        outdir = output / rel_parent
        try:
            result = convert_one(path, engine, images)
            write_result(result, outdir, to)
            status = "OK"
            if result.warnings:
                status = "OK / warnings"
            table.add_row(str(path), result.engine, ", ".join(to), status)
            for warning in result.warnings:
                console.print(f"[yellow]warning:[/yellow] {path}: {warning}")
        except Exception as exc:
            table.add_row(str(path), "-", ", ".join(to), f"FAILED: {exc}")
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
