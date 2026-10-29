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
- **WHEN** watch mode observes a supported file with an unchanged size and modification timestamp in two consecutive snapshots
- **THEN** it submits that file to the existing batch pipeline

#### Scenario: Ignore duplicate snapshots
- **WHEN** watch mode sees a fingerprint already processed
- **THEN** it does not submit that file again unless its fingerprint changes and becomes stable

#### Scenario: Exclude output subtree
- **WHEN** the output directory is within the watched directory
- **THEN** the output subtree is excluded from all input snapshots

#### Scenario: Process changed files again
- **WHEN** a previously processed file has a changed fingerprint and then remains stable across two snapshots
- **THEN** the changed file is submitted to the existing batch pipeline once

#### Scenario: Validate and stop watch mode
- **WHEN** watch mode is enabled for a file, identical source and output directory, or a non-finite or non-positive polling interval
- **THEN** the command reports an input error; Ctrl-C stops a running watcher cleanly

#### Scenario: Stop watching
- **WHEN** the user presses Ctrl-C
- **THEN** the command exits cleanly with a concise message

### Requirement: List available engines
The CLI MUST provide a command that reports registered engines and whether their local runtime is detected.

#### Scenario: List engines
- **WHEN** the user invokes `document-converter list-engines`
- **THEN** the CLI reports each supported engine and its detected availability

### Requirement: Bounded batch concurrency
The `convert` command MUST default `--parallel` to 1, accept values from 1 through 4 inclusive, and reject values outside that range.

#### Scenario: Parallel option is omitted
- **WHEN** the user runs `convert` without `--parallel`
- **THEN** the command processes inputs with one worker

#### Scenario: Parallel option is out of range
- **WHEN** the user provides a value below 1 or above 4
- **THEN** the command reports a parameter error before processing inputs
