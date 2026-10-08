# Development Roadmap

## Current implemented changes

- **CHG-001 — Standalone offline HTML renderer**: implemented in `document_converter/renderer.py` and integrated with the writer. Its OpenSpec change remains in the change history pending review/archive workflow.
- **CHG-002 — Batch parallel processing**: implemented with a default of one worker, a hard limit of four, per-file fault isolation, relative-directory preservation, and collision-safe output names. Its OpenSpec change remains in the change history pending review/archive workflow.
- **PDF text/scanned detection**: already implemented in `document_converter/detector.py` and integrated into engine selection in `document_converter/pipeline.py`. Do not create a new OCR-detection implementation change unless a specific missing behavior is identified.

- **CHG-003 — Watch mode**: implemented and pushed in commit `f572e78`. Uses standard-library polling, stable-file fingerprints, output-subtree exclusion, and existing batch fault isolation. Local-first; no runtime dependency or model is added.

## Active development

- **CHG-004 — Image asset output and reference mapping**: active under `openspec/changes/CHG-004-image-asset-mapping/`. Keeps nested asset paths safe and rewrites matching local Markdown/HTML references in `referenced` mode; no runtime dependency is added.
