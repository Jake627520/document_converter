# Change Proposal: Local Web Workbench

## Why

The converter is currently operated through a terminal. Users need a clear local browser interface to select or drop a supported document, choose Markdown or HTML, run conversion, and download the result.

## What Changes

Add an optional FastAPI web interface and `document-converter web` launcher. The page uses a responsive, accessible workspace layout with a drop zone, selected-file list, Markdown/HTML selection, progress/status feedback, and a download action. Conversion continues through the existing pipeline adapter.

The server binds only to `127.0.0.1`; rejects non-local Host headers; caps request and file sizes; accepts only the pipeline's supported suffixes; stores files under generated names in a temporary directory; and removes temporary data after success or failure. No upload is persisted. Optional Marker and MinerU engines are neither installed nor selected by the website.

## Supported inputs

The website accepts `.pdf`, `.docx`, `.doc`, `.pptx`, `.ppt`, `.xlsx`, `.xls`, `.html`, `.htm`, `.epub`, `.md`, `.markdown`, `.txt`, `.png`, `.jpg`, `.jpeg`, `.webp`, `.csv`, `.rtf`, `.odt`, `.ods`, and `.odp`, matching `document_converter.pipeline.SUPPORTED`.

## Acceptance criteria

- A browser can load an accessible upload form and select `.md` or `.html` output.
- Supported uploads call the existing conversion API and return downloadable output; invalid suffix/format/host and oversized requests are rejected.
- Uploaded file names never become filesystem paths; all temporary input/output data is cleaned on every path.
- The launcher defaults to loopback only and does not enable Marker/MinerU.
- Tests cover validation, mocked conversion success/failure, cleanup, request bounds, host checks, and UI semantics.
- README explains installation, local startup, supported inputs, and the fact that processor/model network behavior is not guaranteed to be offline.
