## Purpose
Define behavior for processing multiple inputs while isolating failures per file.

## Requirements

### Requirement: Isolate input failures
Failure of one input MUST be reported for that input without preventing the remaining batch items from being processed.

#### Scenario: One input fails
- **WHEN** a batch contains a failing input and other processable inputs
- **THEN** the failure is recorded and processing continues for the other inputs
