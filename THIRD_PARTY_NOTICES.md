# Third-party Software and Model Review Notes

This file records dependency roles and project configuration. The upstream license labels below have not been independently verified for the exact resolved package versions, transitive dependencies, or model artifacts used in a deployment. See [docs/LICENSE_AUDIT.md](docs/LICENSE_AUDIT.md) for the open review items.

| Component | Project role | Configuration in this repository | License review status |
|---|---|---|---|
| Docling | Default document engine | Listed in the required dependency range in `pyproject.toml` | Exact package, transitive dependency, and model terms not verified here |
| Marker | Optional PDF engine | Declared under the `marker` extra; adapter invokes a local CLI | Exact package, transitive dependency, model terms, and use conditions not verified here |
| MinerU / Magic-PDF | Optional PDF/OCR engine | Declared under the `mineru` extra; adapter invokes a local CLI | Exact package, transitive dependency, model terms, and use conditions not verified here |
| Typer, Rich | CLI and terminal output | Required dependencies in `pyproject.toml` | Exact resolved license texts not verified here |
| pytest, pytest-cov, pip-audit, pip-licenses | Development and audit tools | Declared under the `dev` extra | Exact resolved license texts not verified here |

The optional-extra and subprocess boundaries describe how this repository is configured; they do not by themselves determine whether a specific use or distribution complies with third-party terms. No commercial-use, copyleft, or model-redistribution clearance is asserted by this file.

Before distribution or commercial deployment, review the exact installed versions, transitive packages, downloaded model artifacts, required notices, and the intended deployment model. The repository's private visibility does not remove those review requirements.
