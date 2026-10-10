# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Model-Free PDF Engine (`docling-native`)**: PDF conversion through Docling's `NativePdfPipeline`, which runs no layout, table or OCR model, so PDFs convert without PyTorch or downloaded model weights. `auto` places it after the model-based engines, and every conversion records its reduced fidelity as a warning (`document_converter/engines/docling_native_engine.py`).
- **`--strip-page-numbers`**: Opt-in removal of lines holding only digits during `--clean`.
- **Shared Synthetic PDF Builders**: `tests/pdf_samples.py` writes structurally valid PDFs (correct cross-reference offsets, font resource, real content stream) so the suite needs no committed PDF fixture.

### Fixed
- **Markdown Cleaner Data Loss**: `--clean` deleted any line holding only 1-4 digits, which removed table values such as a quantity or a year. Those lines are now preserved; labelled page markers (`Page 3 of 12`, `4 / 20`, `- 5 -`) are still removed.
- **Test Suite Could Not Pass From A Fresh Clone**: three CLI and watcher tests required `tests/fixtures/sample_text.pdf`, which `.gitignore`'s `*.pdf` rule keeps out of the repository. They now build their input in a temporary directory.
- **PDF Detection Varied With The Environment**: the built-in stream analyzer classified ordinary text PDFs as `scanned` because it required an end-of-line before `endstream` and decoded only Flate streams. It now tolerates the missing EOL and decodes ASCII85, including ASCII85 wrapping Flate, and `pypdf` is a declared dependency so detection no longer depends on what happens to be installed.
- **Misleading Scanned-PDF Warning**: the pipeline claimed "OCR processing applied" for every scanned PDF, including engines that run no OCR. The warning now names the engine and tells the reader to check the output.

### Changed
- `clean_markdown`, `write_result`, `process_batch` and `DirectoryWatcher` accept `strip_bare_numbers`.
- `AGENTS.md` validation now runs `document-converter list-engines`; `--list-engines` was never a registered option.

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
