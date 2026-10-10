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
- **THEN** the CLI reports PDF page, text-layer, and classification information for PDF inputs, showing a basename for a file source and root-relative paths for directory sources

### Requirement: Select an engine and cleaning behavior
The convert command MUST accept `auto`, `docling`, `docling-native`, `marker` and
`mineru` as engine names and reject any other value. With `--clean`, bare numeric
lines MUST be preserved unless `--strip-page-numbers` is also given.

#### Scenario: Unknown engine name
- **WHEN** the user passes an engine name outside the supported set
- **THEN** the CLI reports an input error listing the supported names

#### Scenario: Opt into bare page-number removal
- **WHEN** the user passes `--clean --strip-page-numbers`
- **THEN** lines holding only digits are removed from the Markdown output

### Requirement: Watch a local input directory
The convert command MUST be able to watch a local directory and convert supported new or changed files after they become stable. Polling MUST use the Python standard library and MUST NOT add runtime dependencies or send local files to a remote service.

#### Scenario: Process stable files once
- **WHEN** a supported file has the same size and modification timestamp in two consecutive snapshots
- **THEN** it is processed through the existing batch pipeline, and that fingerprint is not processed again unless it changes

#### Scenario: Exclude output subtree
- **WHEN** the output directory is within the watched directory
- **THEN** the resolved output subtree is excluded from input discovery

#### Scenario: Validate and stop watch mode
- **WHEN** watch mode is enabled with a file source, identical source/output paths, or a non-finite or non-positive interval
- **THEN** the CLI reports an input error; Ctrl-C stops a running watcher cleanly

### Requirement: List available engines
The CLI MUST provide a command that reports registered engines and whether their local runtime is detected.

#### Scenario: List engines
- **WHEN** the user invokes `document-converter list-engines`
- **THEN** the CLI reports each supported engine and its detected availability
