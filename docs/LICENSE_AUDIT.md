# License and third-party review status

Updated: 2026-10-09.

The intended repository posture is private. Visibility is an access setting, not a license or a compliance finding. This document records evidence and release requirements; it does not establish that every combination or jurisdiction has been legally cleared.

## Original Software and first installer

The original Software uses the custom proprietary `LICENSE`. It permits personal and company internal local use, including internal commercial use. Its resale and redistribution restrictions apply only to material the copyright holder owns or has authority to license. Third-party and non-waivable statutory rights are preserved. This is not MIT or an OSI open source license: the [Open Source Definition](https://opensource.org/osd) requires redistribution rights that this custom grant does not provide.

The copyright marking `Copyright (c) 2026 Jake Chiu` follows the user's instruction to use previous projects' marking style and the verified personal-project source `/Users/jakechiu/Documents/Projects/japanese-kana-learning/LICENSE:3`. It is the marking selected for this release, not a finding that all project rights belong to that individual. Contribution, employment/commission and third-party rights chains remain unverified; the license grants only rights the copyright holder owns or is authorized to license. The root `LICENSE` is authoritative; `docs/LICENSE.proprietary.draft.txt` is a historical copy excluded from distribution.

The first installer is scoped to the local interface and Markdown/plain-text conversion. Docling, PyMuPDF/MuPDF, Marker, MinerU, OCR/PDF engines, and model weights are excluded from this release scope. This is a build requirement, not proof of artifact contents. Only the generated inventory and inspection of the built files can establish the actual contents of a specific package.

## Dated evidence for separately installed engines

The following upstream sources were consulted on 2026-10-09. A verified statement about one package version does not cover its dependencies or models.

| Component | Evidence checked | Consequence and remaining scope |
|---|---|---|
| PyMuPDF 1.28.0 / MuPDF | The upstream [1.28.0 COPYING](https://github.com/pymupdf/PyMuPDF/blob/1.28.0/COPYING) contains AGPL v3; the [official licensing page](https://pymupdf.readthedocs.io/en/latest/about.html#license-and-copyright) describes AGPL and commercial licensing | Do not bundle it under the original Software's restrictive license. A proposed combined distribution or network deployment needs review of the exact code, applicable AGPL obligations, or an appropriate commercial agreement |
| Docling 2.97.0 | Maintainer-published [versioned PyPI page](https://pypi.org/project/docling/2.97.0/) identifies the code license as MIT and states individual model licenses must be consulted; [current upstream LICENSE](https://github.com/docling-project/docling/blob/main/LICENSE) was also read | Exact resolved package license files, transitive dependencies, and actual model/checkpoint terms remain to be collected. The 2.97.0 archive's original license text was not extracted in this review; the current branch text is not a replacement for it |
| Marker 2.0.0 | [Versioned upstream LICENSE](https://github.com/datalab-to/marker/blob/v2.0.0/LICENSE) is Apache-2.0; [versioned README](https://github.com/datalab-to/marker/blob/v2.0.0/README.md#commercial-usage) distinguishes code from modified AI Pubs Open Rail-M model terms and describes commercial limits | Apache-2.0 for code does not grant model rights. Actual Surya and other artifacts, revisions, original terms, use conditions, and any separately acquired commercial license remain unverified |
| MinerU / Magic-PDF | The pre-change repository declared `magic-pdf>=0.9,<2`, while `document_converter/engines/command_engine.py` described a MinerU 4.x command and `cli.py` recommended MinerU 4.x | Package/API mismatch is recorded; no license conclusion is drawn from a different version. Resolve the actual package, executable, version, dependencies, and model artifacts before enabling or distributing this profile |

The local `python3` metadata inspection on 2026-10-09 found PyMuPDF 1.28.0 in `/opt/homebrew/lib/python3.14/site-packages`. It did not find Docling, Marker, Magic-PDF, MinerU, or Surya in that interpreter. This is a developer-environment observation, not the installer inventory. The PDF detector contains `import fitz` in `document_converter/detector.py`; a package need not appear in the project's declared dependencies to be used when available in the runtime environment.

## Review rules for every artifact

- Generate the inventory from the actual isolated build environment and retain exact versions, artifact provenance, and hashes where available. Distinguish included runtime components from build/test/audit tools.
- Collect original `LICENSE`, `COPYING`, `NOTICE`, and required attribution material for all included packages, transitive components, Python, and any bundled bootloader/native code. Inspect content, not only classifier strings.
- Check the built files for engines, model caches, native libraries, downloaded assets, and accidental files. A core profile declaration is insufficient by itself.
- If a license requires source, a source offer, modification marking, or additional notices, satisfy the applicable obligation for the artifact. A copied license alone is insufficient.
- Review separately installed engines against the intended use. Private access, optional extras, subprocesses, and a local server are not automatic exceptions to license terms.
- Keep model weights, checkpoints, datasets, and assets separate from package-code license conclusions. Record actual artifact IDs, revisions, terms, notices, and any use restrictions before they are enabled or shipped.

The security workflow's license check reports on the environment it installs and on the names its tool recognizes. Its presence or a pass is not a full artifact or model review. Review each run's output and independently inspect the release inventory.

## Jurisdiction research boundary

The Taiwan [Copyright Act, articles 10, 11, 12 and 37](https://law.moj.gov.tw/LawClass/LawAll.aspx?PCode=J0070017), consulted on 2026-10-09, provides protection upon completion subject to statutory exceptions, addresses employee/commissioned-work ownership and contractual allocation, and defines licensing by the agreed scope. Protection arising automatically does not prove that all project rights belong to this project's named copyright holder; authorship, employment/commission arrangements, incorporated material and authority to license remain relevant.

Mainland China's [Regulations on Computer Software Protection, articles 14 and 18](https://xzfg.moj.gov.cn/front/law/detail?LawID=581), consulted on 2026-10-09, address protection from completion and licensed use by contract, with exercise of rights limited to those expressly granted. This does not establish ownership of every component or remove third-party terms. Across these jurisdictions, private repository access does not remove applicable copying/distribution duties; contract formation, mandatory rights, and whether a combination triggers additional obligations still require analysis of the actual recipient and artifact.

The United States research consulted on 2026-10-09 records [17 USC section 106](https://www.copyright.gov/title17/92chap1.html) reproduction and distribution rights and [chapter 4](https://www.copyright.gov/title17/92chap4.html) notice and registration provisions. Notice or registration is not a universal prerequisite to protection; an applicable third-party license can still require preserving its notices. Supplier location alone does not decide which country's law governs a transaction or contract; the [Copyright Office international guidance](https://www.copyright.gov/international-issues/) describes territorial protection and international arrangements. The applicable law, contract formation and enforceability for a specific recipient remain case-specific.

[Surya 0.22.1 MODEL_LICENSE](https://raw.githubusercontent.com/datalab-to/surya/v0.22.1/MODEL_LICENSE) was reviewed in the separate research and contains additional commercial, competition and output terms. It is a review lead, not a finding that those terms apply to an unidentified model artifact. The [PyMuPDF licensing page](https://pymupdf.io/licensing) distinguishes commercial licensing and OEM distribution: a future commercial bundle would need the actual agreement to cover its intended redistribution, rather than relying on a general commercial label.

## Unverified decisions

The exact first installer inventory, all transitive license texts and notices, models and optional-engine deployment compatibility remain pending until the relevant build or profile is reviewed. This document gives no conclusion that changing process boundaries avoids copyleft or that proprietary and AGPL material can be combined under these terms. It gives no jurisdiction-specific enforceability opinion or assertion of lawyer approval.

See `PRIVATE_DISTRIBUTION.md` for the release controls and `THIRD_PARTY_NOTICES.md` for notice handling. These files and `LICENSE` accompany the installer in `legal/`; source locations are `docs/PRIVATE_DISTRIBUTION.md`, `THIRD_PARTY_NOTICES.md`, and the root `LICENSE`.
