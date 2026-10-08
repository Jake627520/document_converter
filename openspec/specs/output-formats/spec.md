## Purpose
Define serialization behavior and safety requirements for document conversion outputs.

## Requirements

### Requirement: Write requested output formats
The writer MUST emit requested available formats as UTF-8 files and report when an engine cannot provide a requested representation.

#### Scenario: Engine supplies an output
- **WHEN** the conversion result contains data for a requested format
- **THEN** the writer writes that representation to the output directory

#### Scenario: HTML is absent but Markdown exists
- **WHEN** HTML output is requested and an engine supplies Markdown but no HTML
- **THEN** the built-in renderer writes a complete HTML5 document with embedded styles and no external resources

### Requirement: Escape generated HTML content
The built-in renderer MUST escape source text and the document title, and MUST NOT execute raw HTML.

#### Scenario: Markdown contains HTML-looking text
- **WHEN** rendered Markdown contains markup such as `<script>`
- **THEN** the renderer emits escaped text rather than an active HTML element

### Requirement: Preserve referenced assets
When image extraction is requested, the writer MUST place assets in a sibling assets directory and preserve references relative to the output.

#### Scenario: Conversion result contains image assets
- **WHEN** the result includes named image bytes
- **THEN** the writer writes the bytes beneath the output's assets directory
