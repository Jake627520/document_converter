## MODIFIED Requirements

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
