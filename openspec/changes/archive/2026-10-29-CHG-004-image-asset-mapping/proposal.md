# CHG-004 — Image Asset Output and Reference Mapping

## Proposal

When an engine returns image assets in `referenced` mode, the writer currently saves files under a sibling assets directory but leaves document references pointing at the engine's original paths. This can make both Markdown and HTML outputs refer to files that do not exist beside the generated document.

Update the writer to preserve safe relative asset paths beneath `{output_stem}_assets/`, rewrite only local image references that match returned asset keys, and warn while rejecting unsafe paths and path collisions. Keep processing local and use only the Python standard library.

## Scope

- Map confirmed Markdown image destinations and HTML `<img src>` values in `referenced` mode.
- Preserve nested asset paths and URL-encode path segments in emitted references.
- Reject absolute, drive-qualified, backslash, traversal, symlink-escape, and case-fold-colliding asset paths.
- Keep native engine HTML as the HTML source; only rewrite matched local image `src` values.
- Keep `none` and `embedded` behavior unchanged.

## Acceptance criteria

- Markdown output, native HTML output, and fallback HTML point to files actually written under `{stem}_assets/` for matched assets.
- Nested paths are preserved, and references with spaces or other reserved characters are URL encoded.
- Unsafe asset paths and case-insensitive collisions are skipped with warnings and cannot write outside the asset root.
- External URLs, data URIs, unmatched references, ordinary links, and references in modes other than `referenced` remain unchanged.
- Empty asset sets do not create an asset directory or modify references.
- Regression tests cover the above behavior, with the test phase observed failing before implementation.
- Lint, full tests, diff check, and OpenSpec validation pass in the local environment with CLI dependencies available.
