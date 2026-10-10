## Purpose
Define the reviewed local application release profiles and the guarantees each one makes about what it bundles and accepts.

## Requirements

### Requirement: Keep each release profile explicit and separate
Every packaged local release MUST declare a profile that fixes its accepted input formats, its excluded modules, its pinned distributions, its candidate name and its bundle identifier. Adding a profile MUST NOT change what an existing profile freezes or accepts.

#### Scenario: Profile declares its own audit surface
- **WHEN** a candidate is built for a profile
- **THEN** the build records that profile in the manifest and third-party inventory, and pins the distributions from that profile's own requirement files

#### Scenario: Existing profile is unaffected by a new one
- **WHEN** a new profile is added
- **THEN** the reviewed profile's excluded modules, forbidden frozen entries, forbidden distributions and accepted inputs remain as they were

### Requirement: Text release stays free of engine code
The `text-only` profile MUST accept Markdown and UTF-8 text only, MUST reject every other input, and MUST NOT freeze or load engine, pipeline, detector or CLI modules, any document engine, or a deep-learning runtime.

#### Scenario: PDF reaches the text release
- **WHEN** a PDF is uploaded to the text release
- **THEN** the request is rejected as an unsupported input type

#### Scenario: Forbidden module is frozen
- **WHEN** the build would freeze an engine, pipeline, detector, CLI or document-engine module
- **THEN** the build fails before producing a candidate

### Requirement: PDF release converts text-layer PDFs without model weights
The `pdf-text` profile MUST accept text-layer PDFs in addition to Markdown and UTF-8 text, MUST convert PDFs with the model-free engine only, and MUST NOT bundle or load a deep-learning runtime, the optional engines, or any model weights. It MUST still reject Office and image inputs.

#### Scenario: Text-layer PDF is uploaded
- **WHEN** a PDF carrying a text layer is uploaded
- **THEN** the release returns its Markdown or HTML conversion

#### Scenario: Scanned PDF is uploaded
- **WHEN** a PDF has no text layer and no OCR is available
- **THEN** the release reports that the file has no text layer instead of returning an empty document

#### Scenario: Office or image input is uploaded
- **WHEN** a Word, PowerPoint, Excel or image file is uploaded
- **THEN** the request is rejected as an unsupported input type

#### Scenario: Model runtime is pinned or frozen
- **WHEN** the profile's requirement files or frozen inventory would include a deep-learning runtime or an optional engine
- **THEN** the build fails before producing a candidate

### Requirement: A frozen candidate reports its own profile
A frozen application MUST select its reviewed profile without a command-line argument, and MUST be able to report the profile and its accepted inputs for validation.

#### Scenario: Frozen application starts
- **WHEN** a frozen candidate is launched with no arguments
- **THEN** it configures the profile recorded in its bundle

#### Scenario: Diagnostics are requested
- **WHEN** the candidate is run with the diagnostics flag
- **THEN** it reports the active profile, the accepted input suffixes and that no forbidden module is loaded
