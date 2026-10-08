# Output Formats Specification Delta

## ADDED Requirements

### Requirement: Offline HTML rendering fallback
When an engine returns Markdown but no HTML, the writer MUST render Markdown to a complete HTML5 document using the built-in renderer. Rendering MUST work without network access or additional runtime dependencies, and the generated document MUST use embedded CSS without external stylesheets, scripts, or fonts.

#### Scenario: Markdown is the only available source
- **WHEN** `write_result` receives a result with Markdown and no engine HTML and HTML output is requested
- **THEN** it writes a complete standalone HTML document with rendered block structure and embedded styles
- **AND** it renders headings and paragraph text as semantic HTML elements

#### Scenario: Markdown is empty
- **WHEN** `write_result` receives an empty string as Markdown and HTML output is requested
- **THEN** it writes a complete standalone HTML document with an empty content area

### Requirement: Safe Markdown-to-HTML conversion
The built-in renderer MUST support headings, paragraphs, ordered and unordered lists, tables, fenced code blocks, inline code, bold and italic emphasis, and empty documents. Source text and document titles MUST be escaped as text. Raw HTML MUST NOT be executed. Fenced-code language labels MUST be restricted to safe attribute characters.

#### Scenario: HTML-looking Markdown content
- **WHEN** Markdown includes tags such as `<script>` or `<tag>` in text or table cells
- **THEN** those characters are emitted escaped and cannot create HTML elements

#### Scenario: Fenced code language is malformed
- **WHEN** a code fence language label contains quotes or attribute syntax
- **THEN** the renderer omits the language class rather than emitting an unsafe attribute

### Requirement: Preserve engine HTML
When a conversion engine supplies HTML, the writer MUST write that HTML unchanged and MUST NOT replace it with the Markdown fallback.

#### Scenario: Engine provides native HTML
- **WHEN** HTML output is requested and both native HTML and Markdown are present
- **THEN** the output file contains the native HTML unchanged
