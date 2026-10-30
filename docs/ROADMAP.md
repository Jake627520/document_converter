# Development Roadmap

## Done and archived

Archived on 2026-10-29 under `openspec/changes/archive/`; their requirements are in `openspec/specs/`.

- **CHG-001 — Standalone offline HTML renderer**: `document_converter/renderer.py`, used by the writer when no engine supplies HTML.
- **CHG-002 — Batch parallel processing**: one worker by default, a hard limit of four, per-file fault isolation, relative-directory preservation, and collision-safe output names.
- **CHG-003 — Watch mode**: standard-library polling, stable-file fingerprints, output-subtree exclusion, and the batch fault isolation.
- **CHG-004 — Image asset output and reference mapping**: nested asset paths stay safe; matching local Markdown/HTML references are rewritten in `referenced` mode.
- **CHG-005 — Local web workbench**: loopback-only, cross-site refusal, request/file/count limits, ephemeral uploads, download naming and the model-free note. Its spec, rewritten to match the code (it had listed only `md`/`html` outputs), is the new `openspec/specs/web-workbench/`.
- **CHG-007 — CSP and interface languages**: response security headers and the sandboxed preview in `security-baseline`; the three interface languages and how a request picks one in `web-workbench`.
- **CHG-008 — CJK PDF detection**: CJK text and ToUnicode CMaps count as a text layer; an empty or corrupt PDF is `unknown`, not `scanned`. Already in `openspec/specs/pdf-detection/`, so archived without a spec update.
- **CI cost optimization**: concurrency, `paths-ignore`, timeouts, pip caching and `scripts/local-ci.sh`. Tooling only, archived without a spec update.

PDF text/scanned detection lives in `document_converter/detector.py` and drives engine selection in `document_converter/pipeline.py`. Do not create a new OCR-detection change unless a specific missing behavior is identified.

## Waiting on the owner

- **CHG-006 — Private macOS release**: the candidate builds and its release tests pass. Before distribution the owner confirms the rights owner and recipients and installs on a target machine; a fresh-context acceptance review follows.
- **macOS Developer ID signing and notarization — not planned** (owner's decision, 2026-10-29): the app is not distributed through the App Store, and recipients are few, so it stays signed ad hoc. A recipient opens it once through **System Settings › Privacy & Security › Open Anyway**, as the README describes. Revisit if the app is handed to people who cannot do that; it would need an Apple Developer Program membership, a Developer ID Application certificate, hardened runtime, `notarytool` submission and stapling.

## Next

- **Windows verification** (source install verified, 2026-10-30): the `windows` job in `.github/workflows/test.yml` installs from source with the web extra on `windows-latest` (Python 3.12, no Docling), runs the test suite and the `document-converter --help` and `list-engines` checks. The repo is public, so GitHub-hosted runner minutes are free, Windows included; the double rate for Windows applies only to private repos. `scripts/local-ci.sh` cannot run this job, so its result comes from GitHub. The job passes (229 tests, 5 skipped for want of Docling), and the READMEs say so. Still open: Docling and PDF conversion on Windows have not been checked; a Windows installer is out of scope.
