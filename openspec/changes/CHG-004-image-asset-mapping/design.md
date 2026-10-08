# Design: CHG-004 Image Asset Output and Reference Mapping

## Data flow

`pipeline._process_single_item` passes the selected image mode to `writer.write_result`. In `referenced` mode, the writer normalizes returned asset keys, rejects unsafe paths and case-fold collisions, checks that resolved output paths remain inside the output and asset roots, then creates an exact normalized-key-to-output-URI map. It applies that map to Markdown image destinations and quoted HTML `img src` attributes only. Generated fallback HTML is rendered from the already rewritten Markdown; native engine HTML remains the source when present.

The asset root remains `{output_stem}_assets/`. Relative key components are preserved below that root. URI encoding is applied to the output reference while path separators remain separators. Asset writes create parent directories as needed.

## Safety and compatibility

- Keys containing absolute paths, drive prefixes, backslashes, NUL, empty path components, or `..` components are rejected with warnings.
- Keys that collide after normalization or case folding are all rejected rather than overwriting one another.
- Resolved paths must remain within their output roots, including when pre-existing symlinks are present.
- Only exact local destinations that identify an accepted asset key are rewritten. Schemes, network paths, data URIs, traversal references, normal links, and unknown image references are left unchanged.
- The `none` and `embedded` modes keep existing reference and asset-writing behavior.
- No runtime dependency or extraction engine behavior is added.

## TDD plan

Add focused writer tests first and observe failures against the old API/behavior. Implement mapping and safe path handling, then run the focused tests followed by lint, the full suite, whitespace checking, and OpenSpec validation. CLI integration is verified through the existing `.venv` that includes Typer.
