## ADDED Requirements

### Requirement: Bounded batch concurrency
The `convert` command MUST default `--parallel` to 1, accept values from 1 through 4 inclusive, and reject values outside that range.

#### Scenario: Parallel option is omitted
- **WHEN** the user runs `convert` without `--parallel`
- **THEN** the command processes inputs with one worker

#### Scenario: Parallel option is out of range
- **WHEN** the user provides a value below 1 or above 4
- **THEN** the command reports a parameter error before processing inputs
