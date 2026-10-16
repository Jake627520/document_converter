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

#### Scenario: Every engine fails
- **WHEN** every engine in the chain fails for an input
- **THEN** the pipeline raises one error that keeps each engine's exception, so a caller can tell why each failed without parsing the message

### Requirement: Convert PDFs without model weights
A model-free PDF adapter MUST convert PDF input using only the text and images the
file already contains, without model weights or a deep-learning runtime, and MUST
report its reduced fidelity. Automatic engine selection MUST place it after the
model-based engines so it serves as the fallback that keeps PDF conversion working.

#### Scenario: Model-based engines are unavailable
- **WHEN** a PDF is converted and no model-based engine can run
- **THEN** the model-free adapter converts the file and records a warning that no
  layout, table or OCR model ran

#### Scenario: Scanned page reaches the model-free adapter
- **WHEN** the adapter recovers no text because the PDF has no text layer
- **THEN** it records a warning that no OCR ran rather than reporting usable output

#### Scenario: Non-PDF input
- **WHEN** the model-free adapter is selected for input that is not a PDF
- **THEN** it reports that it cannot handle the input

### Requirement: Keep optional engines optional
Marker and MinerU MUST remain outside the default dependency set and MUST be invoked through their adapters as local command-line tools.

#### Scenario: Optional command is unavailable
- **WHEN** an optional engine executable is not installed
- **THEN** the adapter reports an unavailable-engine error and the pipeline may try another configured fallback

#### Scenario: MinerU converts on this machine
- **WHEN** the MinerU adapter converts an input
- **THEN** it runs `mineru-kit parse` with no remote-service option, and never MinerU's `mineru` command, which has no `kit` subcommand and prepares usage telemetry for every subcommand

#### Scenario: Only MinerU's `mineru` command is installed
- **WHEN** `mineru` is on the path but `mineru-kit` is not
- **THEN** MinerU is reported as unavailable, by the adapter and by `list-engines`, and no process is started
