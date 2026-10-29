# Tasks — CHG-001 Standalone Offline HTML Renderer

## Implementation
- [x] Inspect existing writer, renderer, tests, and repository OpenSpec layout.
- [x] Add regression tests for headings/paragraphs, tables, code fences, escaping, offline output, lists, empty input, and safe code-language attributes.
- [x] Implement built-in renderer for the scoped Markdown constructs with embedded CSS and no runtime dependency.
- [x] Connect HTML fallback in `write_result`; keep engine-provided HTML unchanged.
- [x] Correct the existing table closing tag and code-language attribute handling.
- [x] Add the OpenSpec output-formats delta and align proposal/design with implementation.
- [x] Compare the added draft files; incorporate the useful sample paragraph into the canonical fixtures while keeping the current renderer API and behavior authoritative.

## Verification
- [x] Confirm targeted tests fail on the prior implementation (3 regressions reproduced).
- [x] Run renderer and writer tests after implementation.
- [x] Run complete local unittest suite and lint/compile checks.
- [x] Review final diff and update status after verification.

## Not Performed
- The local CI-equivalent `pytest --cov` command could not run because `pytest` is not installed in this environment; the full `unittest` suite passed.
- No commit, push, or archive was performed. Archive after this change is accepted and merged into baseline specs.
- The early draft's alternate API, stale Red-phase status, and compiled `.pyc` files were not copied into the project.
