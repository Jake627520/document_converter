# Development Roadmap

## Current implemented changes

- **CHG-001 — Standalone offline HTML renderer**: implemented in `document_converter/renderer.py` and integrated with the writer. Its OpenSpec change remains in the change history pending review/archive workflow.
- **CHG-002 — Batch parallel processing**: implemented with a default of one worker, a hard limit of four, per-file fault isolation, relative-directory preservation, and collision-safe output names. Its OpenSpec change remains in the change history pending review/archive workflow.
- **PDF text/scanned detection**: already implemented in `document_converter/detector.py` and integrated into engine selection in `document_converter/pipeline.py`. Do not create a new OCR-detection implementation change unless a specific missing behavior is identified.

## Next candidate

- **CHG-003 — Watch mode**: a candidate for a future proposal to monitor an input directory and convert new or changed files. It is not yet specified or implemented. Before implementation, define stable-file detection, duplicate-event handling, output-directory exclusion, per-file errors, shutdown behavior, and any proposed dependency/license impact in an OpenSpec change.

This roadmap is a planning note; it does not claim that the candidate has been approved or scheduled.
