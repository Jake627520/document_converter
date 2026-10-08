## Purpose
Define the adapter boundary between the conversion pipeline and document-processing engines.

## Requirements

### Requirement: Normalize engine integration
Each engine adapter MUST expose capability detection and conversion through the shared engine interface and return the normalized conversion result.

#### Scenario: Engine can process an input
- **WHEN** an adapter supports the input format and conversion succeeds
- **THEN** it returns a `ConversionResult` with the engine identity and available output data

#### Scenario: Engine cannot process an input
- **WHEN** an adapter does not support the input format
- **THEN** it reports that it cannot handle the input without leaking engine-specific behavior into the CLI

### Requirement: Keep optional engines optional
Marker and MinerU MUST remain outside the default dependency set and MUST be invoked through their adapters as local command-line tools.

#### Scenario: Optional command is unavailable
- **WHEN** an optional engine executable is not installed
- **THEN** the adapter reports an unavailable-engine error and the pipeline may try another configured fallback
