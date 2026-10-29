# CHG-003 — Watch mode

## Problem

Users who convert files arriving in a local folder must repeatedly rerun the command. Watching must not process partially written files or feed generated outputs back into the input queue.

## Proposal

Add `convert --watch` for directory inputs. Poll using Python's standard library, process a supported file only after two consecutive snapshots report the same `(size, mtime_ns)`, and reuse the existing batch pipeline for conversion. Watching remains local-first and introduces no runtime dependency.

## Acceptance criteria

- `--watch` accepts directories only; source and output resolving to the same directory is rejected.
- `--watch-interval` defaults to one second and, when watch mode is enabled, must be finite and greater than zero.
- Existing stable files are processed after two equal snapshots; unchanged fingerprints are processed once, while changed files are processed again after stabilizing.
- The resolved output subtree is excluded when it is inside the source tree.
- Only extensions already supported by `discover_inputs` are watched.
- A stable set is passed to `process_batch`, preserving relative paths, safe worker limits, collision handling, and per-file failure isolation.
- Ctrl-C exits cleanly with a concise message; other errors remain visible.
- Polling, sleeping, and stop detection can be injected in tests without real-time waits.
- No runtime dependency or model is added; no licensing claims are changed.
