# License and third-party review status

Updated: 2026-10-16.

The source repository is public. Visibility is an access setting, not a license or a compliance finding: the original Software stays under the proprietary `LICENSE`, which a public repository neither relaxes nor replaces, and third-party terms apply the same either way. This document records evidence and release requirements; it does not establish that every combination or jurisdiction has been legally cleared.

## Original Software and first installer

The original Software uses the custom proprietary `LICENSE`. It permits personal and company internal local use, including internal commercial use. Its resale and redistribution restrictions apply only to material the copyright holder owns or has authority to license. Third-party and non-waivable statutory rights are preserved. This is not MIT or an OSI open source license: the [Open Source Definition](https://opensource.org/osd) requires redistribution rights that this custom grant does not provide.

The copyright marking `Copyright (c) 2026 Jake Chiu` follows the marking style of the copyright holder's earlier personal projects, as verified in one of them at the time of this review. It is the marking selected for this release, not a finding that all project rights belong to that individual. Contribution, employment/commission and third-party rights chains remain unverified; the license grants only rights the copyright holder owns or is authorized to license. The root `LICENSE` is authoritative.

The first installer, now the `text` profile, is scoped to the local interface and Markdown/plain-text conversion. Docling, PyMuPDF/MuPDF, Marker, MinerU, OCR/PDF engines, and model weights are excluded from it. This is a build requirement, not proof of artifact contents. Only the generated inventory and inspection of the built files can establish the actual contents of a specific package.

A second reviewed profile, `pdf`, was added after this audit was first written and supersedes its "Docling excluded" statement for that profile only. It adds Docling's model-free `NativePdfPipeline` (`docling-slim`, `docling-core`, `docling-parse`) and `pypdfium2` with the PDFium build it ships. It still excludes Docling's model-based pipeline and every model weight, OCR, any deep-learning runtime, PyMuPDF/MuPDF, Marker and MinerU, and its packaging enforces that with forbidden-module and forbidden-distribution checks. The `text` profile's scope is unchanged.

## Dated evidence for separately installed engines

The following upstream sources were consulted on 2026-10-09. A verified statement about one package version does not cover its dependencies or models.

| Component | Evidence checked | Consequence and remaining scope |
|---|---|---|
| PyMuPDF 1.28.0 / MuPDF | The upstream [1.28.0 COPYING](https://github.com/pymupdf/PyMuPDF/blob/1.28.0/COPYING) contains AGPL v3; the [official licensing page](https://pymupdf.readthedocs.io/en/latest/about.html#license-and-copyright) describes AGPL and commercial licensing | Do not bundle it under the original Software's restrictive license. A proposed combined distribution or network deployment needs review of the exact code, applicable AGPL obligations, or an appropriate commercial agreement |
| Docling 2.97.0 | Maintainer-published [versioned PyPI page](https://pypi.org/project/docling/2.97.0/) identifies the code license as MIT and states individual model licenses must be consulted; [current upstream LICENSE](https://github.com/docling-project/docling/blob/main/LICENSE) was also read | Exact resolved package license files, transitive dependencies, and actual model/checkpoint terms remain to be collected. The 2.97.0 archive's original license text was not extracted in this review; the current branch text is not a replacement for it |
| Marker 2.0.0 | [Versioned upstream LICENSE](https://github.com/datalab-to/marker/blob/v2.0.0/LICENSE) is Apache-2.0; [versioned README](https://github.com/datalab-to/marker/blob/v2.0.0/README.md#commercial-usage) distinguishes code from modified AI Pubs Open Rail-M model terms and describes commercial limits | Apache-2.0 for code does not grant model rights. Actual Surya and other artifacts, revisions, original terms, use conditions, and any separately acquired commercial license remain unverified |
| MinerU / Magic-PDF | The pre-change repository declared `magic-pdf>=0.9,<2`, while `document_converter/engines/command_engine.py` described a MinerU 4.x command and `cli.py` recommended MinerU 4.x | Package/API mismatch is recorded; no license conclusion is drawn from a different version. Resolve the actual package, executable, version, dependencies, and model artifacts before enabling or distributing this profile. Resolved on 2026-10-16: see "MinerU's commands and telemetry" below |

The local `python3` metadata inspection on 2026-10-09 found PyMuPDF 1.28.0 in `/opt/homebrew/lib/python3.14/site-packages`. It did not find Docling, Marker, Magic-PDF, MinerU, or Surya in that interpreter. This is a developer-environment observation, not the installer inventory. The PDF detector contains `import fitz` in `document_converter/detector.py`; a package need not appear in the project's declared dependencies to be used when available in the runtime environment.

## `pdf` profile evidence (2026-10-12 and 2026-10-13)

- **Inventory.** The profile pins 60 distributions (`scripts/packaging/requirements-macos-arm64-pdf.txt` and its hash lock). Their recorded license metadata, read from an environment installed from that pinned set on 2026-10-13, is permissive for every runtime distribution except the two listed next: MIT, BSD, Apache-2.0, ISC, PSF, MIT-CMU and similar. No GPL- or AGPL-licensed runtime code is bundled.
- **Weak copyleft and exceptions.** `certifi` (MPL-2.0) and `tqdm` (MPL-2.0 and MIT) are bundled unmodified. PyInstaller is GPL-2.0-or-later with its Bootloader exception, whose shipped text permits distributing the embedded bootloader without restriction from those files; `pyinstaller-hooks-contrib` is a build-time dependency.
- **Docling.** `docling-slim` 2.137.0, `docling-core` 2.101.1 and `docling-parse` 7.22.2 record MIT; the [PyPI page for docling 2.138.0](https://pypi.org/project/docling/) also records MIT. The bundled pipeline loads no model.
- **PDFium components.** The pinned macOS arm64 `pypdfium2` 5.14.0 wheel ships 18 license files under its `dist-info/licenses/`. Read on 2026-10-13, two require a statement in the distribution documentation for executable-only distribution: the FreeType Project License ("based in part of the work of the FreeType Team") and the IJG License ("based in part on the work of the Independent JPEG Group"). `THIRD_PARTY_NOTICES.md` carries both. libpng and zlib request but do not require acknowledgement. FreeType, IJG, libjpeg-turbo and the Unicode/ICU terms forbid use of their names in advertising without permission.
- **Notice collection.** Until 2026-10-12 the collector matched notice files by name only and dropped every file shipped under `<dist-info>/licenses/` with an upstream name, 21 of them for this profile, including the 18 PDFium files above. It now also matches that standardised location. `latex2mathml` 3.81.0 and 3.81.1 ship no license file at all, so the profile pins 3.80.0, which does. `scripts/packaging/audit_notices.py` checks every pinned wheel against the build's own rule without installing it.
- **Built artifact.** A `pdf` candidate built on an Apple Silicon Mac on 2026-10-12 carried 124 notice files across 60 packages, and its frozen application reported no forbidden module loaded (`verification/2026-10-12-macos-pdf-candidate/REPORT.md`).

## Optional engines, re-checked 2026-10-13

These remain outside both profiles. The PyPI metadata and license texts were read again on 2026-10-13:

| Component | Evidence | Consequence |
|---|---|---|
| PyMuPDF 1.28.2 | [PyPI](https://pypi.org/project/pymupdf/) records "Dual Licensed - GNU AFFERO GPL 3.0 or Artifex Commercial License" | Unchanged: not to be bundled under the original Software's terms without a commercial agreement or an AGPL-compliant release |
| MinerU 4.0.12 | [PyPI](https://pypi.org/project/mineru/) records `LicenseRef-MinerU-Open-Source-License`; the [upstream LICENSE](https://github.com/opendatalab/MinerU/blob/master/LICENSE.md) is Apache-2.0 with additional terms: commercial use is permitted without a separate licence unless monthly active users exceed 100 million or monthly revenue exceeds USD 20 million, an online service offered to third parties must indicate prominently that it uses MinerU, and the licence terminates automatically on breach | Supersedes the earlier unresolved row. The older `magic-pdf` 1.3.12 package records AGPL-3.0. MinerU's model artifacts were not reviewed |
| Marker 2.0.0 / Surya 0.22.1 | [PyPI](https://pypi.org/project/marker-pdf/) records Apache-2.0 for both packages' code | Unchanged: the model weights carry the separate terms described above |
| Docling model-based pipeline | Model weights are published on Hugging Face; huggingface.co was unreachable from the review environment, so no model card was read | Not reviewed. Irrelevant to both profiles, which bundle no model |

### MinerU's commands and telemetry (2026-10-16)

The `mineru` 4.0.12 wheel was downloaded from PyPI by version and read without being installed or run:

- It provides two commands. `mineru-kit parse INPUT -o OUTPUT --tier standard` parses on the local machine, and switches to a parse service only with `--remote` (mineru.net) or `--remote-url`. `mineru` has no `kit` subcommand, so the adapter's earlier `mineru kit parse` could not succeed.
- Every `mineru` subcommand runs a root callback that prepares usage telemetry, sent to `https://mineru.net/metrics/v2/metrics`. On first run it asks for consent with yes as the default; `mineru telemetry disable` turns it off. Tracing static imports from `mineru-kit parse` reaches no telemetry module.
- Upstream installs it as `pip install "mineru>=4.0,<5"`, and its base requirements include PyTorch, `huggingface-hub` and `modelscope` for its model files.

Consequences in this repository: the adapter runs only `mineru-kit parse`, with no remote option; `list-engines` detects MinerU by `mineru-kit`; and the `mineru` extra installs `mineru>=4,<5` instead of the AGPL-3.0 `magic-pdf`. MinerU stays outside both release profiles. Its model artifacts were not reviewed, and MinerU itself was not run in the review environment.

## Review rules for every artifact

- Generate the inventory from the actual isolated build environment and retain exact versions, artifact provenance, and hashes where available. Distinguish included runtime components from build/test/audit tools.
- Collect original `LICENSE`, `COPYING`, `NOTICE`, and required attribution material for all included packages, transitive components, Python, and any bundled bootloader/native code. Inspect content, not only classifier strings.
- Check the built files for engines, model caches, native libraries, downloaded assets, and accidental files. A core profile declaration is insufficient by itself.
- If a license requires source, a source offer, modification marking, or additional notices, satisfy the applicable obligation for the artifact. A copied license alone is insufficient.
- Review separately installed engines against the intended use. Optional extras, subprocesses, and a local server are not automatic exceptions to license terms.
- Keep model weights, checkpoints, datasets, and assets separate from package-code license conclusions. Record actual artifact IDs, revisions, terms, notices, and any use restrictions before they are enabled or shipped.

The security workflow's license check reports on the environment it installs and on the names its tool recognizes. Its presence or a pass is not a full artifact or model review. Review each run's output and independently inspect the release inventory.

## Jurisdiction research boundary

The Taiwan [Copyright Act, articles 10, 11, 12 and 37](https://law.moj.gov.tw/LawClass/LawAll.aspx?PCode=J0070017), consulted on 2026-10-09, provides protection upon completion subject to statutory exceptions, addresses employee/commissioned-work ownership and contractual allocation, and defines licensing by the agreed scope. Protection arising automatically does not prove that all project rights belong to this project's named copyright holder; authorship, employment/commission arrangements, incorporated material and authority to license remain relevant.

Mainland China's [Regulations on Computer Software Protection, articles 14 and 18](https://xzfg.moj.gov.cn/front/law/detail?LawID=581), consulted on 2026-10-09, address protection from completion and licensed use by contract, with exercise of rights limited to those expressly granted. This does not establish ownership of every component or remove third-party terms. Across these jurisdictions, repository visibility does not change applicable copying/distribution duties; contract formation, mandatory rights, and whether a combination triggers additional obligations still require analysis of the actual recipient and artifact.

The United States research consulted on 2026-10-09 records [17 USC section 106](https://www.copyright.gov/title17/92chap1.html) reproduction and distribution rights and [chapter 4](https://www.copyright.gov/title17/92chap4.html) notice and registration provisions. Notice or registration is not a universal prerequisite to protection; an applicable third-party license can still require preserving its notices. Supplier location alone does not decide which country's law governs a transaction or contract; the [Copyright Office international guidance](https://www.copyright.gov/international-issues/) describes territorial protection and international arrangements. The applicable law, contract formation and enforceability for a specific recipient remain case-specific.

[Surya 0.22.1 MODEL_LICENSE](https://raw.githubusercontent.com/datalab-to/surya/v0.22.1/MODEL_LICENSE) was reviewed in the separate research and contains additional commercial, competition and output terms. It is a review lead, not a finding that those terms apply to an unidentified model artifact. The [PyMuPDF licensing page](https://pymupdf.io/licensing) distinguishes commercial licensing and OEM distribution: a future commercial bundle would need the actual agreement to cover its intended redistribution, rather than relying on a general commercial label.

## Unverified decisions

The exact first installer inventory, all transitive license texts and notices, models and optional-engine deployment compatibility remain pending until the relevant build or profile is reviewed.

Parts of the original Software were written with an AI coding assistant, as the repository's commit history records. Under the United States Copyright Office's January 2025 report on copyrightability, protection extends to human creative contribution - selection, arrangement and modification - but not to material whose expression an AI system determined, and prompting alone is not authorship. The share of protectable human authorship in the AI-assisted portions has not been assessed, in Taiwan or elsewhere. This bears on how far the proprietary license can be enforced over those portions, not on the third-party terms above. This document gives no conclusion that changing process boundaries avoids copyleft or that proprietary and AGPL material can be combined under these terms. It gives no jurisdiction-specific enforceability opinion or assertion of lawyer approval.

See `PRIVATE_DISTRIBUTION.md` for the release controls and `THIRD_PARTY_NOTICES.md` for notice handling. These files and `LICENSE` accompany the installer in `legal/`; source locations are `docs/PRIVATE_DISTRIBUTION.md`, `THIRD_PARTY_NOTICES.md`, and the root `LICENSE`.
