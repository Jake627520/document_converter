## Purpose
Define the local document-conversion command interface and its user-visible options.

## Requirements

### Requirement: Convert local documents
The CLI MUST accept a file or directory and support Markdown, HTML, JSON, and plain-text output selection.

#### Scenario: Convert a file
- **WHEN** the user invokes `document-converter convert` with a supported input file
- **THEN** the CLI processes it using the selected engine and output formats

#### Scenario: Inspect PDF text layers
- **WHEN** the user invokes `document-converter inspect` with a file or directory
- **THEN** the CLI reports PDF page, text-layer, and classification information for PDF inputs

### Requirement: List available engines
The CLI MUST provide a command that reports registered engines and whether their local runtime is detected.

#### Scenario: List engines
- **WHEN** the user invokes `document-converter list-engines`
- **THEN** the CLI reports each supported engine and its detected availability
