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

#### Scenario: Docling JSON is requested from the text release
- **WHEN** the text release is asked for Docling JSON
- **THEN** the page does not offer it and the request is refused, because the release runs no engine that could produce one

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

### Requirement: Office and OCR release reads with the operating system's OCR
The `office-ocr` profile MUST accept Word, PowerPoint and Excel (`.docx`, `.pptx`, `.xlsx`), PDFs, images (`.png`, `.jpg`, `.jpeg`, `.webp`), Markdown and UTF-8 text. It MUST read Office files with the model-free Office adapter, MUST read a PDF's text layer first and use OCR only when none is found, and MUST recognize text with the OCR built into macOS. It MUST NOT bundle or load an OCR engine, a deep-learning runtime, the optional engines or any model weights, and MUST keep every restriction of the `pdf-text` profile.

#### Scenario: A Word, PowerPoint or Excel file is uploaded
- **WHEN** a `.docx`, `.pptx` or `.xlsx` file is uploaded
- **THEN** the release returns its conversion, read without OCR

#### Scenario: A scanned PDF or an image is uploaded
- **WHEN** a PDF without a text layer, or an image, is uploaded on macOS
- **THEN** the release recognizes its text with the operating system's OCR and says the text was recognized

#### Scenario: A PDF with a text layer is uploaded
- **WHEN** a PDF carries a text layer
- **THEN** the release reads that layer and does not run OCR

#### Scenario: Legacy Office or another format is uploaded
- **WHEN** a `.doc`, `.ppt`, `.xls` or other unlisted file is uploaded
- **THEN** the request is rejected as an unsupported input type

#### Scenario: An OCR engine or model runtime is pinned or loaded
- **WHEN** the profile's requirement files or frozen inventory would include an OCR engine, a model runtime or an optional engine, or one of their modules loads at launch
- **THEN** the build fails, or the launcher refuses to start

### Requirement: Offer only the outputs a release can produce
Every release MUST offer Markdown, HTML and plain text. A release MUST offer Docling JSON only when it runs an engine that produces one, and MUST explain, rather than fail without reason, when a given input yields none.

#### Scenario: Docling JSON from the pdf release
- **WHEN** the pdf release is asked for Docling JSON
- **THEN** a PDF yields the Docling document, and a Markdown or text input is refused with the reason that no engine parsed it

### Requirement: A frozen candidate reports its own profile
A frozen application MUST select its reviewed profile without a command-line argument, and MUST be able to report the profile and its accepted inputs and outputs for validation.

#### Scenario: Frozen application starts
- **WHEN** a frozen candidate is launched with no arguments
- **THEN** it configures the profile recorded in its bundle

#### Scenario: Diagnostics are requested
- **WHEN** the candidate is run with the diagnostics flag
- **THEN** it reports the active profile, the accepted input suffixes, the output formats it can produce and that no forbidden module is loaded

### Requirement: Collect every notice a pinned wheel ships
A candidate build MUST copy each pinned distribution's own license material out of the installed wheel, recognising it both by file name and by the standardised `<dist-info>/licenses/` location, whose file names follow the upstream project rather than any convention. A build MUST fail rather than produce a candidate for a distribution that ships no license material at all.

#### Scenario: Wheel ships its notices under the standard location
- **WHEN** a pinned wheel declares license files that the installer records under `<dist-info>/licenses/`, named after the components they cover
- **THEN** the build collects every one of them into the candidate's third-party notices and records each path with its SHA-256

#### Scenario: Wheel ships no license material
- **WHEN** a pinned wheel carries no license file in any recognised form, and no reviewed source-distribution notice exists for that exact release
- **THEN** the build fails and names that distribution, and the profile pins a release that does ship its notice

#### Scenario: Wheel ships none but its source distribution does
- **WHEN** a reviewed notice taken from the release's source distribution is recorded with that archive's SHA-256 and the member read
- **THEN** the build collects that notice, records its source and hash in the inventory, and the notice audit re-reads it from the source distribution

#### Scenario: Code is named like a notice
- **WHEN** a compiled extension, source file or debug-symbol bundle outside `<dist-info>/licenses/` has a name such as `copying`
- **THEN** it is not counted as license material
