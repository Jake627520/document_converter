# 5. Licensing and compliance

**English** | [繁體中文](05-licensing-and-compliance.zh-TW.md) | [简体中文](05-licensing-and-compliance.zh-CN.md)

The project's own code is under a custom license; it ships about sixty other
people's packages inside its app. Both facts have to hold at once. The evidence
is in [`docs/LICENSE_AUDIT.md`](../LICENSE_AUDIT.md) and
[`THIRD_PARTY_NOTICES.md`](../../THIRD_PARTY_NOTICES.md); this chapter is how it
got there.

> This is a record of what was checked, not legal advice. The audit says the same
> about itself.

## Choosing what to ship by its license

The licensing work started before any code was bundled: what went into the app
was chosen partly by what its license would let the app do.

| Candidate | License | Outcome |
| --- | --- | --- |
| PyMuPDF / MuPDF | AGPL-3.0, or an Artifex commercial license | **Not shipped.** AGPL would reach the whole app; a commercial license costs money the project did not need to spend |
| `pypdfium2` + PDFium | BSD-3-Clause or Apache-2.0; PDFium's components permissive | **Shipped** in the `pdf` profile as the PDF reader |
| Docling, model-free pipeline | MIT | **Shipped** in the `pdf` profile. Its model-based pipeline is not, and its models were never reviewed |
| Marker | Apache-2.0 code; model weights under separate terms with commercial limits | Optional engine, installed by the user, never bundled |
| MinerU 4.x | Apache-2.0 with added terms: a licence is needed above 100 million monthly users or USD 20 million monthly revenue, and an online service must say it uses MinerU | Optional engine, never bundled. The older `magic-pdf` package is AGPL-3.0 |

"Optional" carries no legal weight by itself. An engine the user installs keeps
its own terms; the audit records them so a user who installs one can see what
they have agreed to.

## What the `pdf` app actually contains

| | |
| --- | --- |
| Packages | 60, pinned by hash |
| GPL or AGPL runtime code | None |
| Weak copyleft | `certifi` and `tqdm` (MPL-2.0), bundled unmodified — MPL obligations attach to modified files |
| PyInstaller | GPL-2.0-or-later **with its Bootloader exception**, which permits shipping the bootloader inside an app without the GPL reaching the app |
| PDFium | One binary carrying 15 component licenses: FreeType, libjpeg-turbo, ICU, libpng, zlib, OpenJPEG, Little CMS, Abseil and others |
| Notices in the built app | 124 files across 60 packages, in `Contents/Resources/legal/` |

## Reading the licenses, not their labels

A license label — "BSD", "MIT" — says what kind of terms apply. It does not
say what those terms ask of you. Reading the 15 PDFium component licenses one by
one found two that **require** a sentence in the distribution's documentation
when only the compiled program is shipped:

- *This software is based in part on the work of the FreeType Team.*
- *This software is based in part on the work of the Independent JPEG Group.*

Both are now in `THIRD_PARTY_NOTICES.md`, which travels with every installer.
The first pass found only FreeType. IJG's requirement is in a file of its own,
`libjpeg_turbo.ijg`, and turned up only when every shipped license file was read
in full. Four of the licenses also forbid using their authors' names
in advertising, so the acknowledgements are worded as documentation, not
endorsement.

## When the notices went missing

The build collected license files by name — `LICENSE`, `COPYING`, `NOTICE`.
Packages built to the current standard
([PEP 639](https://peps.python.org/pep-0639/)) keep theirs in a `licenses/`
folder, under whatever name upstream gave them, such as `freetype.txt`. All 21
of those were dropped without a word, including the 18 from `pypdfium2`.

It surfaced on the owner's Mac, when the build stopped because `latex2mathml`
had no notice at all. Looking into why showed that versions 3.81.0 and 3.81.1
ship no license file, and that the collector had a second, quieter gap. The
fix in [#5](https://github.com/Jake627520/document_converter/pull/5):

- match the standard location as well as the names;
- pin `latex2mathml` to 3.80.0, which does ship its license;
- add `scripts/packaging/audit_notices.py`, which downloads every pinned wheel by
  its hash and checks it against the build's own rule, without installing
  anything — so the question can be answered before a build, from any machine.

The build failing loudly was the good outcome. The 21 dropped notices had
produced no error at all.

## Documents written for a different project

The legal documents were written for the first app, which bundled no document
engine. Then the `pdf` profile added Docling and PDFium — and the documents
still said Docling was excluded. Nothing checks prose against a dependency list.

It was caught when the owner asked for the licensing to be confirmed once more
before going public, and fixed in
[#6](https://github.com/Jake627520/document_converter/pull/6). The rule taken
from it: **a change to what ships is a change to the legal documents**, in the
same pull request.

## Public is not open source

The repository is public; the license did not change. The custom
[`LICENSE`](../../LICENSE) permits personal use and a company's internal use,
including internal commercial use, and restricts resale and redistribution of
the original code. That is not an open-source license — the
[Open Source Definition](https://opensource.org/osd) requires the freedom to
redistribute.

Being public adds one thing: GitHub's terms let anyone view the repository and
fork it on GitHub. The README's fork instructions say what that does and does
not allow. Third-party terms are the same whether the repository is public or
private.

## Rebuilding a component to avoid its license

One question came up while weighing the options: could reverse-engineering
tools be used to rebuild a restrictively licensed component as the project's
own?

Not in a way that removes the terms. Code rebuilt from another program's
decompiled or disassembled form is still derived from it, and many licenses
forbid reverse engineering outright. The routes that work are the ones this
project used or kept open:

- **choose a permissively licensed alternative** — PDFium instead of MuPDF;
- **buy the commercial license**, where one is offered;
- **clean-room implementation** — written from a public specification by people
  who have not studied the original. That is a legal process with its own
  records, not something a coding agent can assert about itself.

## AI-assisted authorship

Most of this code was written by an AI coding agent. The
[US Copyright Office's January 2025 report](https://www.copyright.gov/ai/) holds
that protection covers human creative contribution — selecting, arranging,
modifying — and not expression an AI system determined; prompting alone is not
authorship. How much of this project is protectable has not been assessed.

That affects how far the project's own license can be enforced over its own
code. It changes nothing about third-party terms, which bind the project either
way. The audit records it as an open question, which is what it is.
