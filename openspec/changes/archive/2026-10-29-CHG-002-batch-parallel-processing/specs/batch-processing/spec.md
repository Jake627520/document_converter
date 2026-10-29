## ADDED Requirements

### Requirement: Bounded batch concurrency
The batch processor MUST default to one worker and MUST accept only worker counts from 1 through 4 inclusive. The CLI and pipeline MUST reject values outside this range.

#### Scenario: Default worker count
- **WHEN** the caller omits `--parallel`
- **THEN** the batch uses one worker

#### Scenario: Worker count exceeds the limit
- **WHEN** the caller requests fewer than 1 or more than 4 workers
- **THEN** the CLI or pipeline rejects the request without starting batch work

### Requirement: Collision-safe batch output
Batch processing MUST preserve source-relative directories and MUST NOT silently overwrite outputs from distinct inputs. It MUST compare normalized destination paths case-insensitively and disambiguate colliding stems deterministically, including when no `source_root` is supplied.

#### Scenario: Same stem with different extensions
- **WHEN** two inputs in the same relative directory have the same stem but different extensions
- **THEN** each input's output uses a distinct name derived from its source extension

#### Scenario: Remaining output name collision
- **WHEN** source extensions do not produce unique output stems
- **THEN** a stable source-path digest is appended to each colliding output stem

#### Scenario: Nested input directories
- **WHEN** files with the same name are found under different source subdirectories
- **THEN** each output remains under the corresponding relative subdirectory

#### Scenario: Case-only collision without a source root
- **WHEN** inputs would produce destination paths differing only by letter case and no `source_root` is supplied
- **THEN** the batch assigns distinct output names before starting workers
