import concurrent.futures
import hashlib
from pathlib import Path
from .engines.base import EngineError
from .engines.docling_engine import DoclingEngine
from .engines.docling_native_engine import DoclingNativePdfEngine
from .engines.command_engine import MarkerEngine, MinerUEngine
from .engines.text_direct_engine import TextDirectEngine
from .models import ConversionResult, ImageMode
from .detector import inspect_pdf, PdfProfile
from .writer import write_result
from .formats import SUPPORTED

DEFAULT_PARALLEL = 1
MAX_WORKER_LIMIT = 4

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
        "text_direct": TextDirectEngine(),
        "docling": DoclingEngine(),
        "docling-native": DoclingNativePdfEngine(),
        "marker": MarkerEngine(),
        "mineru": MinerUEngine(),
    }
    if name != "auto":
        if name not in engines:
            raise EngineError(f"Unknown engine: {name}")
        engine = engines[name]
        if not engine.can_handle(path):
            raise EngineError(f"{name} cannot handle {path.suffix}")
        return [engine]

    # Auto engine selection strategy
    suffix = path.suffix.lower()
    is_pdf = suffix == ".pdf"
    is_image = suffix in {".png", ".jpg", ".jpeg", ".webp"}
    is_text = suffix in {".md", ".markdown", ".txt"}

    if is_text:
        # Prefer the zero-dependency reader; Docling remains a fallback only if
        # the caller forced a non-auto engine (handled above).
        return [engines["text_direct"]]
    if is_pdf and profile and profile.is_scanned:
        # Scanned PDF without text layer: prioritize engines with dedicated OCR/VLM
        # capabilities, then fall back to the model-free reader as a last resort.
        return [engines["docling"], engines["mineru"], engines["marker"], engines["docling-native"]]
    elif is_pdf:
        # The model-free PDF reader runs last: it needs no model weights, so it keeps
        # conversion working where the model-based engines are unavailable.
        return [engines["docling"], engines["marker"], engines["mineru"], engines["docling-native"]]
    elif is_image:
        return [engines["docling"], engines["marker"], engines["mineru"]]
    else:
        return [engines["docling"]]

def convert_one(path: Path, engine_name: str, image_mode: ImageMode) -> ConversionResult:
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    profile: PdfProfile | None = None
    if path.suffix.lower() == ".pdf":
        try:
            profile = inspect_pdf(path)
        except Exception:
            profile = None

    errors: list[str] = []
    failures: list[Exception] = []
    for engine in choose_engine(engine_name, path, profile=profile):
        try:
            result = engine.convert(path, image_mode)
            if profile:
                result.metadata["pdf_profile"] = profile
                if profile.classification == "scanned":
                    result.warnings.append(
                        f"Scanned PDF detected ({profile.page_count} pages, {profile.total_chars} text chars). "
                        f"Text recovery depends on OCR support in the {result.engine} engine; "
                        "check the output before relying on it."
                    )
                elif profile.classification == "hybrid":
                    result.warnings.append(
                        f"Sparse text or mixed PDF detected ({profile.page_count} pages, {profile.total_chars} text chars). "
                        f"Some content may require OCR support in the {result.engine} engine."
                    )
            return result
        except Exception as e:
            errors.append(f"{engine.name}: {e}")
            failures.append(e)
    raise EngineError("All engines failed:\n" + "\n".join(errors), failures=failures)

def _process_single_item(
    path: Path,
    output_dir: Path,
    formats: list[str],
    engine_name: str,
    image_mode: str,
    clean: bool,
    preserve_layout: bool,
    source_root: Path | None,
    output_stem: str,
    strip_bare_numbers: bool = False,
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
            output_stem=output_stem,
            image_mode=image_mode,
            strip_bare_numbers=strip_bare_numbers,
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
    parallel: int = DEFAULT_PARALLEL,
    source_root: Path | None = None,
    strip_bare_numbers: bool = False,
) -> list[dict]:
    """
    Process a list of input documents sequentially or in parallel.
    Fault-tolerant: individual file errors do not abort the overall batch.
    Rejects unsafe worker counts instead of silently increasing or clamping them.
    """
    if parallel < 1 or parallel > MAX_WORKER_LIMIT:
        raise ValueError(f"parallel must be between 1 and {MAX_WORKER_LIMIT}")

    # Preserve nested source directories. If inputs would otherwise target the
    # same output stem, add the extension and, for remaining collisions, a
    # stable digest of the source identity.
    output_stems: dict[Path, str] = {}
    groups: dict[tuple[str, str], list[Path]] = {}
    source_is_dir = source_root is not None and source_root.is_dir()
    for path in inputs:
        rel_path = path.relative_to(source_root) if source_is_dir else Path(path.name)
        # macOS commonly uses case-insensitive filesystems. Group the normalized
        # destination before assigning names so case-only variants cannot race
        # to write the same file when no source_root is supplied.
        output_parent = rel_path.parent.as_posix().casefold()
        groups.setdefault((output_parent, path.stem.casefold()), []).append(path)

    for paths in groups.values():
        if len(paths) == 1:
            output_stems[paths[0]] = paths[0].stem
            continue
        paths = sorted(paths, key=lambda item: (item.as_posix().casefold(), item.as_posix()))
        stem = paths[0].stem
        candidates: dict[str, list[Path]] = {}
        for path in paths:
            candidates.setdefault(f"{stem}_{path.suffix.lower().lstrip('.')}", []).append(path)
        for candidate, colliding_paths in candidates.items():
            for path in colliding_paths:
                identity = (
                    path.relative_to(source_root).as_posix()
                    if source_is_dir
                    else path.as_posix()
                )
                digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:8]
                output_stems[path] = (
                    candidate if len(colliding_paths) == 1 else f"{candidate}_{digest}"
                )

    if parallel == 1 or len(inputs) <= 1:
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
                output_stem=output_stems[p],
                strip_bare_numbers=strip_bare_numbers,
            )
            for p in inputs
        ]

    # Parallel execution with a hard resource-safe worker limit.
    workers = parallel
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
                output_stems[p],
                strip_bare_numbers,
            ): p
            for p in inputs
        }
        for future in concurrent.futures.as_completed(future_to_path):
            results.append(future.result())

    # Return results sorted by input path order
    path_order = {p: i for i, p in enumerate(inputs)}
    results.sort(key=lambda r: path_order.get(r["path"], 0))
    return results
