# Release requirements

- Bootstrap a dedicated system-site-packages-disabled environment from hash-pinned official PyPI binary wheels, without copying `.venv` or installing dev/test packages.
- Bind the shared FastAPI UI to loopback; use its existing admission, Host, Origin, upload-size and temporary-file boundaries.
- The launcher permanently selects text-only. Markdown/TXT convert to MD/HTML; PDF/Office/images and invalid UTF-8 cannot fall back to an engine. UI describes the actual inputs.
- Source and frozen launch diagnostics must show no detector/pipeline/engine/AGPL/model imports. Frozen inventory rejects forbidden modules and external site-packages.
- Missing legal documents, wheel notice texts or native runtime provenance must fail before packaging.
- Preserve original notices and exact name/version/role/hash inventory both beside and inside the app. Create ZIP and SHA-256 without modifying existing candidates.
- Mark candidates as not distribution-ready until independent review and rights, signing, recipient and target-machine decisions are resolved. Do not publish or change visibility.
