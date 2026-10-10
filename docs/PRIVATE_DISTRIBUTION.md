# Private source and local installer distribution

Updated: 2026-10-09.

The source repository is intended to remain private. The copyright holder may provide local installation packages to intended recipients under the accompanying custom proprietary `LICENSE`. Recipients may use the original Software personally or for their company's own internal operations, including internal commercial use. Except for permitted internal employee copies, recipients may not resell or redistribute the original Software or modified versions. Third-party components retain their own licenses and rights.

## Final license and historical draft

The final root `LICENSE` is the authoritative license for the original Software and carries `Copyright (c) 2026 Jake Chiu`. This follows the user's instruction to use the marking style of previous projects and the verified personal-project example `japanese-kana-learning/LICENSE:3`. The choice of marking does not establish the complete chain of copyright ownership or authority to license every contribution.

The repository-only file `docs/LICENSE.proprietary.draft.txt` is retained as a historical drafting copy and is not included in installation packages. Its earlier copyright-holder placeholder has been resolved in the final root `LICENSE`; it must not be distributed or substituted for that final file. Each package must carry the complete final root `LICENSE` alongside its applicable third-party material and pass the artifact review described below.

## First release scope

The first installer is limited to the local interface and Markdown/plain-text conversion. PDF, Office, OCR and model-backed conversion are outside this release scope. The build must exclude Docling, PyMuPDF/MuPDF, Marker, MinerU, their model weights and other PDF/OCR engines; inspecting the actual artifact is required to confirm this. A dependency already installed in a developer's global Python environment is not an approved bundle component.

Other engines may be considered later after their exact packages, dependencies, model artifacts and intended use have been reviewed. A user who installs an engine separately must comply with that engine's terms; the original Software's personal/internal-use permission does not grant rights in it.

## Documents carried with each installer

The build places these files under `legal/` beside the distributed application and embeds the same directory at `Document Converter.app/Contents/Resources/legal/`:

1. `LICENSE` with the original Software's complete terms and copyright notice.
2. `THIRD_PARTY_NOTICES.md` with the explanation of independent third-party rights.
3. `LICENSE_AUDIT.md` and this `PRIVATE_DISTRIBUTION.md` with the release scope and review limits.
4. `THIRD_PARTY_INVENTORY.json`, generated for the build, with exact versions, runtime versus build-only roles, and the paths to original license and notice material; the build also carries the resolved `requirements*.lock` files.
5. `third-party/<package>/` with the original license, copyright, `NOTICE` and attribution texts required for actual included components, including the Python runtime and bundled bootloader/native code.

The inventory is generated for each build. These source documents do not substitute for it and do not assert that a build has already passed review. A web link or an SPDX label alone does not replace a required original notice. Keep source/offer material with the artifact where its license requires it.

## Before handing over a package

- Inspect the final inventory and files against the release scope. Resolve missing license texts, unidentified components and applicable source/notice obligations before release.
- Present the original Software's terms before installation or first use and keep them accessible afterward. Record the package version and checksum with the provided terms; do not claim this alone establishes enforceable assent in every jurisdiction.
- Provide accurate instructions for the included formats and local operation. Do not advertise excluded PDF/Office/OCR features or an engine/model's commercial clearance.
- Keep internal copies with the original copyright, license and third-party material. Apply the recipient restrictions only to the original Software, preserving independent third-party rights.

## Review boundary

The custom license is a reviewable expression of the authorized personal/internal-use terms. It does not promise zero legal risk or lawyer approval. Its disclaimer is limited by applicable law, and mandatory rights remain effective. Applicable contract formation, consumer rules, intellectual-property ownership and license compatibility may depend on the recipient, jurisdiction and exact distribution.

MIT release is deferred. Making the repository public or releasing under MIT would require a separate decision, confirmation of rights in the original material, and review of the then-current artifacts. A future change must state which release it covers; these documents make no advance promise to relicense current copies.
