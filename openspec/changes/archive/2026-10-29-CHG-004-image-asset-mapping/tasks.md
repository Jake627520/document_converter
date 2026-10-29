# Tasks

- [x] Define image reference mapping behavior, compatibility modes, and path safety rules.
- [x] Add writer regression tests for Markdown/HTML mapping, nesting, external/data URIs, invalid paths, collisions, compatibility modes, and empty assets.
- [x] Observe the new tests fail before implementation.
- [x] Implement safe asset path normalization, reference rewriting, and writer/pipeline image-mode wiring.
- [x] Add/verify symlink escape rejection and native HTML non-local reference preservation.
- [x] Run lint, full tests, diff check, OpenSpec validation, and CLI tests in the existing `.venv`.
