# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
