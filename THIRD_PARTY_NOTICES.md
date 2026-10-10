# Third-party components and notices

Updated: 2026-10-09.

Document Converter's original code is covered by the custom proprietary `LICENSE`. That license permits personal and company internal use, including internal commercial use, and restricts resale and redistribution of the original Software. **Those restrictions do not apply to third-party components.** Each third-party component retains its own license, notices, and rights; its applicable terms prevail for that component.

## What accompanies an installation package

This repository file describes the notice policy. It is not a complete inventory of a particular installer. The build carries a `legal/` directory beside the distributed application and embeds the same tree at `Document Converter.app/Contents/Resources/legal/`. It must contain:

- The original Software's `LICENSE`, this file, and the distribution and audit documents.
- `legal/THIRD_PARTY_INVENTORY.json`, generated from the build, with exact packages, versions, runtime/build roles, and collected license/notice paths; `requirements*.lock` records the resolved environments.
- Original license texts, copyright notices, and required `NOTICE` or attribution files under `legal/third-party/<package>/`, plus the Python runtime and its included component material.

The package's generated inventory and collected original texts identify what that build includes. A license label or URL in a table does not replace a required license or notice text. Missing or unidentified terms must be resolved before that component is distributed. Components with source, offer, attribution, or other obligations require those obligations to be addressed in addition to copying a license file.

## Installation profiles

| Profile or component | Role | Distribution boundary |
|---|---|---|
| First core local installer | Local interface and Markdown/plain-text conversion | The release scope excludes Docling, PyMuPDF/MuPDF, Marker, MinerU, downloaded model weights, and OCR/PDF engines; verify the actual build inventory and files before release |
| Typer, Rich and local web dependencies | CLI, output, local interface | Exact installed versions and transitive dependencies come from the build inventory |
| Python runtime and standard library | Executable runtime | Include the actual runtime's license material and any bundled component notices |
| Docling | Separately installed document engine | Code and model terms are reviewed separately; not cleared for inclusion by its MIT code label alone |
| PyMuPDF/MuPDF | PDF analyzer available in some developer environments | AGPL/commercial licensing requires a separate decision; absent from the core release scope |
| Marker/Surya | Separately installed PDF/OCR engine and models | Code and model licenses are distinct; absent from the core release scope |
| MinerU/Magic-PDF | Separately installed PDF/OCR engine | Version/API and exact artifact license review remain separate; absent from the core release scope |
| Build, test and audit tools | Development and build environment | Being installed in the build environment does not mean a tool ships to users; bundled bootloader/runtime code still needs its applicable notices |

Private repository visibility, optional dependencies, and subprocess invocation do not establish license compliance. Installing an engine separately does not override its own terms or resolve whether a particular combined use is permitted.

See `LICENSE_AUDIT.md` and `PRIVATE_DISTRIBUTION.md` in the package's `legal/` directory for the dated evidence, unresolved review items, and release procedure (source paths: `docs/LICENSE_AUDIT.md` and `docs/PRIVATE_DISTRIBUTION.md`). No model license or commercial-use clearance for an optional engine is granted by this file.
