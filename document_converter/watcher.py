"""Local, standard-library directory polling for watch mode."""

import time
import math
from pathlib import Path
from typing import Callable

from .pipeline import discover_inputs, process_batch


def validate_watch_paths(source: Path, output_dir: Path) -> tuple[Path, Path]:
    """Validate watch directories and return their resolved paths."""
    if not source.is_dir():
        raise ValueError("--watch requires a directory source")
    source_resolved = source.resolve()
    output_resolved = output_dir.resolve()
    if source_resolved == output_resolved:
        raise ValueError("Watch source and output directory must be different")
    return source_resolved, output_resolved


def validate_watch_interval(watch_enabled: bool, interval: float) -> None:
    """Validate the polling interval only when watch mode is active."""
    if watch_enabled and (not math.isfinite(interval) or interval <= 0):
        raise ValueError("--watch-interval must be a finite value greater than 0")


def snapshot_directory(source: Path, output_dir: Path) -> dict[Path, tuple[int, int]]:
    """Return supported input fingerprints, excluding output subtree."""
    source_resolved = source.resolve()
    output_resolved = output_dir.resolve()
    try:
        output_resolved.relative_to(source_resolved)
        output_is_inside_source = output_resolved != source_resolved
    except ValueError:
        output_is_inside_source = False
    result: dict[Path, tuple[int, int]] = {}
    for path in discover_inputs(source):
        resolved = path.resolve()
        if output_is_inside_source:
            try:
                resolved.relative_to(output_resolved)
            except ValueError:
                pass
            else:
                continue
        stat = path.stat()
        result[path] = (stat.st_size, stat.st_mtime_ns)
    return result


class DirectoryWatcher:
    """Track stable fingerprints and submit each changed file once."""

    def __init__(
        self,
        source: Path,
        output_dir: Path,
        *,
        formats: list[str] | None = None,
        engine_name: str = "auto",
        image_mode: str = "none",
        clean: bool = False,
        preserve_layout: bool = False,
        parallel: int = 1,
        strip_bare_numbers: bool = False,
        snapshot_fn: Callable[[Path, Path], dict[Path, tuple[int, int]]] = snapshot_directory,
    ):
        self.source, self.output_dir = validate_watch_paths(source, output_dir)
        self.formats = formats or ["md"]
        self.engine_name = engine_name
        self.image_mode = image_mode
        self.clean = clean
        self.preserve_layout = preserve_layout
        self.parallel = parallel
        self.strip_bare_numbers = strip_bare_numbers
        self.snapshot_fn = snapshot_fn
        self.previous: dict[Path, tuple[int, int]] = {}
        self.processed: dict[Path, tuple[int, int]] = {}

    def poll_once(self) -> list[dict]:
        current = self.snapshot_fn(self.source, self.output_dir)
        ready = [
            path for path, fingerprint in current.items()
            if self.previous.get(path) == fingerprint
            and self.processed.get(path) != fingerprint
        ]
        self.previous = current
        if not ready:
            return []
        results = process_batch(
            inputs=ready,
            output_dir=self.output_dir,
            formats=self.formats,
            engine_name=self.engine_name,
            image_mode=self.image_mode,
            clean=self.clean,
            preserve_layout=self.preserve_layout,
            parallel=self.parallel,
            source_root=self.source,
            strip_bare_numbers=self.strip_bare_numbers,
        )
        # Mark every submitted fingerprint, including isolated failures, so an
        # unchanged bad file does not flood the terminal on every poll.
        for path in ready:
            self.processed[path] = current[path]
        return results


def watch_directory(
    source: Path,
    output_dir: Path,
    *,
    interval: float = 1.0,
    stop_fn: Callable[[], bool] = lambda: False,
    sleep_fn: Callable[[float], None] = time.sleep,
    snapshot_fn: Callable[[Path, Path], dict[Path, tuple[int, int]]] = snapshot_directory,
    on_results: Callable[[list[dict]], None] | None = None,
    **options,
) -> None:
    """Poll until stopped; injected hooks keep the loop testable."""
    validate_watch_interval(True, interval)
    watcher = DirectoryWatcher(source, output_dir, snapshot_fn=snapshot_fn, **options)
    while not stop_fn():
        results = watcher.poll_once()
        if results and on_results:
            on_results(results)
        sleep_fn(interval)
