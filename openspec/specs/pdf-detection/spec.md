## Purpose
Classify PDFs by their extractable text layer to inform local engine selection and inspection output.

## Requirements

### Requirement: Inspect PDF text layer
The detector MUST return a PDF profile describing page count, extracted text, image presence, and a classification of `text_based`, `scanned`, `hybrid`, or `unknown`.

#### Scenario: PDF has extractable text
- **WHEN** a PDF has at least 25 effective characters per page on average (with CJK ideographs/hangul/kana weighted for semantic density)
- **THEN** it is classified as `text_based`

#### Scenario: CJK digital PDF detection
- **WHEN** a PDF contains Traditional Chinese, Simplified Chinese, Japanese, or Korean digital text layer (including Type 0 composite fonts, ToUnicode CMaps, and hex string operators)
- **THEN** the detector extracts text and classifies it as `text_based`, preventing false scanned classification

#### Scenario: PDF is image-based with little or no text
- **WHEN** a PDF has fewer than 10 effective text characters and contains images
- **THEN** it is classified as `scanned`

#### Scenario: PDF has sparse or partial text
- **WHEN** a PDF falls between those thresholds or contains a mixture of text-bearing and sparse pages with images
- **THEN** it is classified as `hybrid`

#### Scenario: Corrupted, empty, or unparseable file
- **WHEN** a file is 0 bytes, missing PDF magic header, or structurally corrupted
- **THEN** the detector classifies it as `unknown` with `is_scanned=False` and `has_text_layer=False`, avoiding premature scanned diagnosis

### Requirement: Use available local analyzers with fallback
PDF inspection MUST prefer available local PDF libraries and fall back to the built-in stream analyzer when those libraries are unavailable.

#### Scenario: Optional PDF library is absent
- **WHEN** no optional PDF parsing library is installed
- **THEN** inspection attempts the built-in analyzer without requiring network access

#### Scenario: Built-in analyzer reads content streams and ToUnicode CMaps
- **WHEN** a text PDF stores its content stream with FlateDecode, ASCII85Decode, or ASCII85 wrapping Flate, using literal strings or hex strings with ToUnicode CMap
- **THEN** the built-in analyzer decodes text and CJK mappings, reporting its text layer and classifying it consistently with library analyzers

