import concurrent.futures
from pathlib import Path
from .engines.base import EngineError
from .engines.docling_engine import DoclingEngine
from .engines.command_engine import MarkerEngine, MinerUEngine
from .models import ConversionResult, ImageMode
from .detector import inspect_pdf, PdfProfile
from .writer import write_result

SUPPORTED = {
    ".pdf", ".docx", ".doc", ".pptx", ".ppt", ".xlsx", ".xls",
    ".html", ".htm", ".epub", ".md", ".markdown", ".txt",
    ".png", ".jpg", ".jpeg", ".webp", ".csv", ".rtf", ".odt", ".ods", ".odp"
}

DEFAULT_MAX_WORKERS = 4
MAX_WORKER_LIMIT = 8

def discover_inputs(source: Path) -> list[Path]:
    if source.is_file():
        return [source]
    if source.is_dir():
        return sorted(
            p for p in source.rglob("*")
            if p.is_file() and p.suffix.lower() in SUPPORTED
        )
    raise FileNotFoundError(source)

def choose_engine(name: str, path: Path, profile: PdfProfile | None = None):
    engines = {
        "docling": DoclingEngine(),
        "marker": MarkerEngine(),
        "mineru": MinerUEngine(),
    }
    if name != "auto":
        engine = engines[name]
        if not engine.can_handle(path):
            raise EngineError(f"{name} cannot handle {path.suffix}")
        return [engine]

    # Auto engine selection strategy
    is_pdf = path.suffix.lower() == ".pdf"
    is_image = path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}

    if is_pdf and profile and profile.is_scanned:
        # Scanned PDF without text layer: prioritize engines with dedicated OCR/VLM capabilities
        return [engines["docling"], engines["mineru"], engines["marker"]]
    elif is_pdf or is_image:
        return [engines["docling"], engines["marker"], engines["mineru"]]
    else:
        return [engines["docling"]]

def convert_one(path: Path, engine_name: str, image_mode: ImageMode) -> ConversionResult:
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    # Lightweight direct handler for markdown and text files if Docling is unavailable or for testing
    if path.suffix.lower() in {".md", ".markdown", ".txt"} and engine_name == "auto":
        try:
            content = path.read_text(encoding="utf-8")
            return ConversionResult(
                source=path,
                engine="text_direct",
                markdown=content,
                text=content,
            )
        except Exception:
            pass

    profile: PdfProfile | None = None
    if path.suffix.lower() == ".pdf":
        try:
            profile = inspect_pdf(path)
        except Exception:
            profile = None

    errors = []
    for engine in choose_engine(engine_name, path, profile=profile):
        try:
            result = engine.convert(path, image_mode)
            if profile:
                result.metadata["pdf_profile"] = profile
                if profile.is_scanned:
                    result.warnings.append(
                        f"Scanned PDF detected ({profile.page_count} pages, {profile.total_chars} text chars). OCR processing applied."
                    )
            return result
        except Exception as e:
            errors.append(f"{engine.name}: {e}")
    raise EngineError("All engines failed:\n" + "\n".join(errors))

def _process_single_item(
    path: Path,
    output_dir: Path,
    formats: list[str],
    engine_name: str,
    image_mode: str,
    clean: bool,
    preserve_layout: bool,
    source_root: Path | None,
) -> dict:
    rel_parent = path.parent.relative_to(source_root) if (source_root and source_root.is_dir()) else Path(".")
    target_outdir = output_dir / rel_parent
    try:
        result = convert_one(path, engine_name, image_mode)
        write_result(
            result=result,
            output_dir=target_outdir,
            formats=formats,
            clean=clean,
            preserve_layout=preserve_layout,
        )
        return {
            "path": path,
            "success": True,
            "engine": result.engine,
            "warnings": result.warnings,
            "metadata": result.metadata,
        }
    except Exception as exc:
        return {
            "path": path,
            "success": False,
            "error": str(exc),
            "warnings": [],
            "metadata": {},
        }

def process_batch(
    inputs: list[Path],
    output_dir: Path,
    formats: list[str],
    engine_name: str = "auto",
    image_mode: str = "none",
    clean: bool = False,
    preserve_layout: bool = False,
    parallel: int = 1,
    source_root: Path | None = None,
) -> list[dict]:
    """
    Process a list of input documents sequentially or in parallel.
    Fault-tolerant: individual file errors do not abort the overall batch.
    Clamps workers to MAX_WORKER_LIMIT to prevent system OOM with local models.
    """
    if parallel <= 1 or len(inputs) <= 1:
        # Sequential execution
        return [
            _process_single_item(
                path=p,
                output_dir=output_dir,
                formats=formats,
                engine_name=engine_name,
                image_mode=image_mode,
                clean=clean,
                preserve_layout=preserve_layout,
                source_root=source_root,
            )
            for p in inputs
        ]

    # Parallel execution with bounded workers
    workers = min(max(parallel, 1), MAX_WORKER_LIMIT)
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_path = {
            executor.submit(
                _process_single_item,
                p,
                output_dir,
                formats,
                engine_name,
                image_mode,
                clean,
                preserve_layout,
                source_root,
            ): p
            for p in inputs
        }
        for future in concurrent.futures.as_completed(future_to_path):
            results.append(future.result())

    # Return results sorted by input path order
    path_order = {p: i for i, p in enumerate(inputs)}
    results.sort(key=lambda r: path_order.get(r["path"], 0))
    return results
