# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Model-Free PDF Engine (`docling-native`)**: PDF conversion through Docling's `NativePdfPipeline`, which runs no layout, table or OCR model, so PDFs convert without PyTorch or downloaded model weights. `auto` places it after the model-based engines, and every conversion records its reduced fidelity as a warning (`document_converter/engines/docling_native_engine.py`).
- **`--strip-page-numbers`**: Opt-in removal of lines holding only digits during `--clean`.
- **macOS `pdf` Release Profile**: the packaged local app can accept text-layer PDFs. `scripts/packaging/profiles.py` declares the reviewed profiles, `bootstrap_macos.sh` takes `RELEASE_PROFILE=pdf`, the launcher reads its profile from the frozen bundle, and `requirements-macos-arm64-pdf.lock` pins 60 hash-locked wheels with no PyTorch, no optional engines and no model weights. A scanned PDF is reported as having no text layer instead of returning an empty document. The reviewed `text` profile is unchanged.
- **`audit_notices.py`**: checks that every wheel a profile pins carries its own license notice, reading each released wheel named by the lock file's hash without installing it, so a dependency bump can be verified from any machine with network access rather than only on the target Mac (`scripts/packaging/audit_notices.py`).
- **macOS VM Verification SOP**: `docs-release/macos-vm-verification.md` walks a candidate through a clean macOS guest - the two risks that only appear on someone else's machine. It transfers the ZIP by HTTP so the quarantine attribute is really applied and Gatekeeper really blocks, then runs `--diagnostics` on a guest with no Python to prove the app is self-contained. States what it does not cover: chip generations and macOS major versions. Needs no second Mac and no paid account; Apple's licence allows two macOS VMs per Apple Silicon host.
- **Shared Synthetic PDF Builders**: `tests/pdf_samples.py` writes structurally valid PDFs (correct cross-reference offsets, font resource, real content stream) so the suite needs no committed PDF fixture.

### Fixed
- **Release Notices Were Collected By File Name Only**: the packaging step matched notice files by name, so it silently dropped every notice a wheel ships under the standardised `<dist-info>/licenses/` location with an upstream name, and refused the build outright for a wheel that ships nothing else. The `pdf` profile lost 21 notice files that way, including the 18 covering PDFium's bundled components (`abseil`, `freetype`, `icu`, `libjpeg-turbo`, `libpng`, `zlib` and more) that `pypdfium2` ships, and `tqdm`'s `LICENCE`. Notices are now recognised by name - including the British spelling - and by that standard location (`scripts/packaging/collect_notices.py`). The reviewed `text` profile's collected set is unchanged.
- **`latex2mathml` Pinned To A Release That Ships No License**: 3.81.0 and 3.81.1 omit the license file from both the wheel and the sdist, so the `pdf` build had no notice to collect for a dependency it redistributes. The profile pins 3.80.0, the last release that ships it, which still satisfies `docling-core`'s `>=3.77.0,<4.0.0`.
- **Markdown Cleaner Data Loss**: `--clean` deleted any line holding only 1-4 digits, which removed table values such as a quantity or a year. Those lines are now preserved; labelled page markers (`Page 3 of 12`, `4 / 20`, `- 5 -`) are still removed.
- **Test Suite Could Not Pass From A Fresh Clone**: three CLI and watcher tests required `tests/fixtures/sample_text.pdf`, which `.gitignore`'s `*.pdf` rule keeps out of the repository. They now build their input in a temporary directory.
- **PDF Detection Varied With The Environment**: the built-in stream analyzer classified ordinary text PDFs as `scanned` because it required an end-of-line before `endstream` and decoded only Flate streams. It now tolerates the missing EOL and decodes ASCII85, including ASCII85 wrapping Flate, and `pypdf` is a declared dependency so detection no longer depends on what happens to be installed.
- **Misleading Scanned-PDF Warning**: the pipeline claimed "OCR processing applied" for every scanned PDF, including engines that run no OCR. The warning now names the engine and tells the reader to check the output.
- **Secret Scan Never Ran On A Push**: the TruffleHog step passed the default branch as `base` and `HEAD` as `head`, which are the same commit on a push to `main`, so it stopped with "BASE and HEAD commits are the same" before scanning. It now scans the commits each event adds: a pull request's base against its head, or the range a push advanced.

### Changed
- `clean_markdown`, `write_result`, `process_batch` and `DirectoryWatcher` accept `strip_bare_numbers`.
- `AGENTS.md` validation now runs `document-converter list-engines`; `--list-engines` was never a registered option.

### Removed
- **Python 3.10 Support**: `requires-python` is now `>=3.11,<3.15` and the CI matrix tests 3.11 and 3.12. `tests/test_security_baseline.py` imports `tomllib`, which entered the standard library in 3.11, so the suite has never been collectable on 3.10 and the job aborted before any test ran. The README already recommended 3.11 or 3.12.

## [0.2.0] - 2026-10-08

### Added
- **OpenSpec Driven Architecture**: Introduced canonical `openspec/specs/` baseline specifications for CLI interface, engine adapters, output serialization, security, and PDF text-layer detection.
- **PDF Text-Layer vs Scanned Auto-Detection**: Zero-dependency built-in PDF stream analyzer and metadata profiling (`document_converter.detector`).
- **Markdown Cleaner**: `--clean` mode with fenced code block and LaTeX math formula preservation, excessive whitespace compression, and page number noise elimination (`document_converter.cleaner`).
- **Layout Preservation**: `--preserve-layout` flag to maintain exact page break spacing.
- **CLI Inspect Subcommand**: `document-converter inspect` to quickly diagnose PDF text layer presence and classification.
- **Test Fixtures & TDD Suite**: Synthesized `sample_text.pdf`, `sample_scanned.pdf`, and full test suite covering CLI, cleaner, pipeline, detector, writer, and security baseline.
- **CI Pipelines**: Matrix testing pipeline (`.github/workflows/test.yml`) with code coverage alongside existing security audit.

### Security & Licensing
- Strictly isolated `marker` (GPL-3.0) and `mineru` (AGPL-3.0 / CC-BY-NC) into `optional-dependencies`.
- Documented third-party code & model licenses in `THIRD_PARTY_NOTICES.md` and `docs/LICENSE_AUDIT.md`.
- Established strict `.gitignore` data leak prevention for credentials, documents, and model checkpoints.

## [0.1.0] - 2026-10-08
- Initial architecture with Docling primary engine, Typer CLI, and multi-format output writer.
