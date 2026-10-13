# Third-party components and notices

Updated: 2026-10-13.

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
| `text` profile installer | Local interface and Markdown/plain-text conversion | Bundles no document engine. Excludes Docling, PyMuPDF/MuPDF, Marker, MinerU, model weights, and OCR/PDF engines; verify the actual build inventory and files before release |
| `pdf` profile installer | The `text` profile plus PDFs that already carry a text layer | Adds Docling's model-free PDF reader and its dependencies (below). Runs no model and bundles no model weights, no OCR engine, no deep-learning runtime, and none of PyMuPDF/MuPDF, Marker or MinerU; verify the actual build inventory and files before release |
| Docling (`docling-slim`, `docling-core`, `docling-parse`) | Model-free PDF reader, `pdf` profile only | MIT. Only the `NativePdfPipeline`, which runs no model, is bundled. Docling's model-based pipeline and its model weights are not bundled and remain a separate review |
| `pypdfium2` and the PDFium build it ships | PDF parsing, `pdf` profile only | BSD-3-Clause or Apache-2.0 for the binding. The PDFium binary comes with 15 further license files covering PDFium itself and the components built into it (FreeType, libjpeg-turbo, ICU, libpng, zlib, OpenJPEG, Little CMS, Abseil, and others), collected as shipped; two of them require the acknowledgements below |
| Typer, Rich and local web dependencies | CLI, output, local interface | Exact installed versions and transitive dependencies come from the build inventory |
| Python runtime and standard library | Executable runtime | Include the actual runtime's license material and any bundled component notices |
| Docling model-based pipeline and models | Separately installed document engine | Not bundled in either profile. Code and model terms are reviewed separately; its MIT code label does not clear the models |
| PyMuPDF/MuPDF | PDF analyzer available in some developer environments | AGPL-3.0 or an Artifex commercial license; requires a separate decision. Absent from both profiles |
| Marker/Surya | Separately installed PDF/OCR engine and models | Code is Apache-2.0; model weights carry separate terms with commercial limits. Absent from both profiles |
| MinerU/Magic-PDF | Separately installed PDF/OCR engine | MinerU 4.x uses the MinerU Open Source License (Apache-2.0 with additional terms); the earlier `magic-pdf` package is AGPL-3.0. Model artifacts are reviewed separately. Absent from both profiles |
| Build, test and audit tools | Development and build environment | Being installed in the build environment does not mean a tool ships to users; bundled bootloader/runtime code still needs its applicable notices |

## Required acknowledgements (`pdf` profile)

A `pdf` profile installer distributes the PDFium build that `pypdfium2` ships, in executable form. Two of its component licenses require a statement in the distribution documentation when only executable code is distributed. This file accompanies every installer in `legal/` and makes those statements:

- **This software is based in part on the work of the FreeType Team.** (FreeType Project License, binary redistribution.)
- **This software is based in part on the work of the Independent JPEG Group.** (IJG License clause 2, as libjpeg-turbo's terms restate it.)

libjpeg-turbo also requires the text of its Modified BSD License in product documentation where the TurboJPEG API is included or used; that text is collected as shipped, beside the other component licenses under `legal/third-party/pypdfium2/`. zlib and libpng ask for an acknowledgement but do not require one.

FreeType, the Independent JPEG Group, libjpeg-turbo and the Unicode/ICU copyright holders do not permit their names to be used in advertising or promotion without prior written permission. These acknowledgements are documentation, not endorsement, and must not be presented as either.

## Other terms that accompany specific components

- `certifi` and `tqdm` are MPL-2.0 (tqdm together with MIT). They are bundled unmodified; MPL-2.0 obligations attach to modified covered files, and the unmodified source is available at the pinned versions on PyPI.
- PyInstaller is GPL-2.0-or-later **with its Bootloader exception**, which permits embedding the compiled bootloader in a program and distributing the result without restriction from the use of those files. `pyinstaller-hooks-contrib` is used at build time.
- Every other bundled distribution of the `pdf` profile is under a permissive license (MIT, BSD, Apache-2.0, ISC, PSF, MIT-CMU or similar) as recorded in its own metadata; the collected texts in `legal/third-party/` are authoritative over that summary.

Private repository visibility, optional dependencies, and subprocess invocation do not establish license compliance. Installing an engine separately does not override its own terms or resolve whether a particular combined use is permitted.

See `LICENSE_AUDIT.md` and `PRIVATE_DISTRIBUTION.md` in the package's `legal/` directory for the dated evidence, unresolved review items, and release procedure (source paths: `docs/LICENSE_AUDIT.md` and `docs/PRIVATE_DISTRIBUTION.md`). No model license or commercial-use clearance for an optional engine is granted by this file.
