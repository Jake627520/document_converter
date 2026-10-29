# Design: Watch mode

`document_converter.watcher` owns path validation, standard-library polling, stable-file detection, output subtree exclusion, and processed fingerprint state. A poll compares the current `(size, mtime_ns)` map with the previous map. Matching entries are stable; only fingerprints different from the last processed fingerprint are submitted. The output subtree is excluded only when the resolved output path is a strict descendant of the resolved source path; an output directory above the source must not hide source files. The source and output resolving to the same path remains invalid.

The watcher submits each newly stable group through the existing `process_batch` API with the watched directory as `source_root`. Failed individual conversions are still returned as results by the batch pipeline; the watcher records their fingerprints too, avoiding repeated error output until the source changes.

The CLI validates watch arguments before entering the loop. A finite positive polling interval is required only when watch mode is enabled. `watch_directory` accepts injected snapshot, sleep, and stop functions for deterministic tests. The production defaults use `time.sleep` and an always-false stop predicate. The command catches only `KeyboardInterrupt` and prints a short stop message.

All inspection and conversion stays on the local filesystem. No watcher library, OCR engine, or model is installed or bundled by this change.
