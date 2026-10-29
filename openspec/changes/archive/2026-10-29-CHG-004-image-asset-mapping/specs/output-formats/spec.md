# Output Formats Specification Delta

## MODIFIED Requirements

### Requirement: Preserve engine HTML
When a conversion engine supplies HTML, the writer MUST preserve it as the HTML source and MUST NOT replace it with the Markdown fallback. In `referenced` image mode, it MAY rewrite only local `<img src>` attributes matching accepted returned assets; all other HTML content MUST remain unchanged.

#### Scenario: Engine provides native HTML
- **WHEN** HTML output is requested and both native HTML and Markdown are present
- **THEN** the output file uses native HTML rather than Markdown fallback
- **AND** its content remains unchanged except for matched local image `src` values in `referenced` mode

### Requirement: Preserve referenced assets
When image extraction is requested in `referenced` mode, the writer MUST write accepted assets beneath the output's `{stem}_assets/` directory while preserving their safe relative path. It MUST rewrite only local Markdown image destinations and HTML `<img src>` values that match an accepted asset key so the output points to the written file. Output URI paths MUST be URL encoded while preserving path separators. Unsafe paths and path collisions MUST be rejected with warnings and MUST NOT write outside the asset root. External URLs, data URIs, unmatched references, and ordinary links MUST remain unchanged. The `none` and `embedded` modes MUST preserve existing behavior.

#### Scenario: Markdown references a returned image asset
- **WHEN** `referenced` mode returns a Markdown image destination matching an asset key
- **THEN** the writer stores the bytes under `{stem}_assets/<safe-relative-path>`
- **AND** the Markdown destination points to that stored file using an encoded relative URI

#### Scenario: Native HTML references a returned image asset
- **WHEN** `referenced` mode returns native HTML with an `<img src>` matching an asset key
- **THEN** the writer preserves the native HTML document and rewrites only that `src` to the stored asset file

#### Scenario: Markdown fallback HTML includes a returned image asset
- **WHEN** HTML output is generated from Markdown that references an accepted asset
- **THEN** the standalone HTML contains an image element pointing to the stored local asset

#### Scenario: Unsafe or colliding asset path
- **WHEN** an asset key is absolute, drive-qualified, contains traversal or backslashes, escapes through a symlink, or collides after case folding
- **THEN** the writer skips the affected asset, records a warning, and does not write outside the asset root
- **AND** references to rejected assets remain unchanged

#### Scenario: External, embedded, or unmatched reference
- **WHEN** an image destination is a remote URL, data URI, or does not match a returned asset key
- **THEN** the writer leaves that destination unchanged

#### Scenario: Non-referenced image mode
- **WHEN** image mode is `none` or `embedded`
- **THEN** the writer preserves existing asset and reference behavior without reference mapping
