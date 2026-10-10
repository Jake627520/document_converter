## Purpose
Classify PDFs by their extractable text layer to inform local engine selection and inspection output.

## Requirements

### Requirement: Inspect PDF text layer
The detector MUST return a PDF profile describing page count, extracted text, image presence, and a classification of `text_based`, `scanned`, or `hybrid` when analysis succeeds.

#### Scenario: PDF has extractable text
- **WHEN** a PDF has at least 25 extracted characters per page on average
- **THEN** it is classified as `text_based`

#### Scenario: PDF is image-based with little or no text
- **WHEN** a PDF has fewer than 10 total text characters and contains images, or has no extractable text
- **THEN** it is classified as `scanned`

#### Scenario: PDF has sparse or partial text
- **WHEN** a PDF falls between those thresholds or contains a mixture of text-bearing and sparse pages
- **THEN** it is classified as `hybrid`

### Requirement: Use available local analyzers with fallback
PDF inspection MUST prefer available local PDF libraries and fall back to the built-in stream analyzer when those libraries are unavailable.

#### Scenario: Optional PDF library is absent
- **WHEN** no optional PDF parsing library is installed
- **THEN** inspection attempts the built-in analyzer without requiring network access

#### Scenario: Built-in analyzer reads a common content-stream encoding
- **WHEN** a text PDF stores its content stream with FlateDecode, ASCII85Decode, or
  ASCII85 wrapping Flate, with or without an end-of-line before `endstream`
- **THEN** the built-in analyzer reports its text layer and classifies it as
  `text_based`, matching the classification an optional library reports
