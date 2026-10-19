# 3. Ten things that looked fine

**English** | [繁體中文](03-silent-failures.zh-TW.md) | [简体中文](03-silent-failures.zh-CN.md)

Each of these was a check, a guard or an output that **looked correct**. Most
reported success. Two looked like a different, smaller problem. None looked like
what it was.

| # | Looked like | Actually | Fixed in |
| --- | --- | --- | --- |
| 1 | Secret scan: ✅ on every push | Read **0 commits** | [#4](https://github.com/Jake627520/document_converter/pull/4) |
| 2 | Dependency audit: ❌, our own package unauditable | Never reached the packages it exists to check — **two real advisories** behind it | [#2](https://github.com/Jake627520/document_converter/pull/2) |
| 3 | Test suite: ✅ | **16 web tests skipped** in CI, the web interface measured at 0% | [#1](https://github.com/Jake627520/document_converter/pull/1) |
| 4 | Test suite: ✅ | Passed **only on the machine that had a gitignored file** | [#1](https://github.com/Jake627520/document_converter/pull/1) |
| 5 | PDF detector: correct | The **same PDF** got a different answer depending on what was installed | [#1](https://github.com/Jake627520/document_converter/pull/1) |
| 6 | `--clean`: conversion clean | **Deleted `84` from a table** as if it were a page number | [#1](https://github.com/Jake627520/document_converter/pull/1) |
| 7 | License notices: collected | **21 silently dropped**, including 18 for PDFium's components | [#5](https://github.com/Jake627520/document_converter/pull/5) |
| 8 | App ships its legal documents | They described **a scope the app did not have** | [#6](https://github.com/Jake627520/document_converter/pull/6) |
| 9 | Conversion: 200 OK | **A 97-byte file holding nothing** | [#7](https://github.com/Jake627520/document_converter/pull/7) |
| 10 | Page shows the file size | **24.0 MB on the page, 25.2 MB in Finder** — same file | [#7](https://github.com/Jake627520/document_converter/pull/7) |

---

## 1. A secret scan that scanned nothing

**Looked like:** TruffleHog green on every push to `main`.

**Actually:** the step compared the default branch with `HEAD`. On a push to
`main` those are the same commit, so it stopped with *"BASE and HEAD commits are
the same"* in under a tenth of a second — having read nothing.

**Found by:** reading the job's log and duration, not its result. A secret scan
over real commits does not finish in 0.05 s.

**Fix:** scan exactly what each event adds — a pull request's base against its
head, a push's range — and skip on branch creation, where there is no range.

**Evidence:** the first push after merging scanned `26f798b..3b451a1`: 7 chunks,
4,055 bytes, 0 secrets.

## 2. A dependency audit that never reached the dependencies

**Looked like:** a red audit job, failing on the project's own package — which
is not on PyPI, so `pip-audit --strict` cannot audit it.

**Actually:** that failure came first and stopped everything, so the
third-party packages — the reason the job exists — were never checked.

**Found by:** asking what the job would report if that one failure were removed.
The first proposed fix was wrong; six variants were tested before the one that
works, which uninstalls the project before auditing.

**Then:** with the audit finally running, it reported **two real advisories** —
one in pytest, whose fix the project's own version pin had been blocking, and
one in setuptools. Both were upgraded.

## 3. Sixteen tests skipped, counted as passing

**Looked like:** a green suite.

**Actually:** CI installed the `dev` extra but not `web`, so every web-interface
test skipped itself. Skipped is not failed, so nothing turned red — and the
whole web interface was measured at 0% coverage in CI.

**Found by:** the coverage gate, once new code tipped the total to 76%, under
its 80% threshold.

**Fix:** CI installs `.[dev,web]`, and the 16 web tests run on every push. The
nine release runtime tests, which need the packaged app's own environments, were
still skipped in CI for a while; a separate job now builds those environments,
runs them, and fails if any skips
([Chapter 4](04-verification-strategy.md#the-packaged-apps-tests-run-in-ci-against-pinned-versions)).

## 4. Tests that only passed on one machine

**Looked like:** a green suite.

**Actually:** three tests read `tests/fixtures/sample_text.pdf`. The repository's
`.gitignore` excludes `*.pdf` — correctly, so a real document cannot be committed
by accident — which meant the file existed only on the machine that created it.
From a fresh clone, the suite could not pass.

**Found by:** running the suite from a clean clone.

**Fix:** the tests now build their own valid PDFs in code (`tests/pdf_samples.py`).
No PDF needs to be committed, and the `.gitignore` rule stays.

## 5. The same PDF got a different answer on a different machine

**Looked like:** a detector that classified PDFs correctly.

**Actually:** with `pypdf` installed, a text PDF was read as text. Without it, a
built-in fallback took over — and called the same file *scanned*, because it
expected a line break before `endstream` and could decode only one compression
format. `pypdf` was not even a declared dependency, so whether it was present
was luck.

**Found by:** comparing the two analyzers on the same files.

**Fix:** `pypdf` is declared; the fallback tolerates the missing line break and
decodes ASCII85. A test now requires both analyzers to agree.

## 6. A cleaner that deleted data

**Looked like:** `--clean` removing page numbers.

**Actually:** it removed every line holding only one to four digits. Engines put
table cells on their own lines — so an LED count of `84` disappeared from a spec
sheet, and the conversion reported success.

**Found by:** converting a spec sheet that contained a table, and checking the
values rather than the layout.

**Fix:** bare numbers are kept by default. Labelled markers such as `Page 3 of 12`
are still removed; stripping bare numbers is now opt-in, `--strip-page-numbers`,
for a reader who accepts what it costs.

## 7. License notices, silently dropped

**Looked like:** the packaging step collecting each dependency's license.

**Actually:** it matched files by name — `LICENSE`, `COPYING`, `NOTICE`. Packages
that declare their licenses in metadata install them under `dist-info/licenses/`
with whatever name the upstream project chose: `Apache-2.0.txt`, `freetype.txt`,
or `LICENCE` in British spelling. All of those were skipped without a word —
**21 files**, including the 18 that cover PDFium's bundled components.

It failed only once: on a package with nothing a name could match. That package,
`latex2mathml`, turned out to be an upstream regression — its 3.81 releases ship
no license file at all.

**Found by:** the owner's first real build on a Mac, which stopped on that one
package. Investigating the one failure surfaced the 21 silent ones.

**Fix:** notices are matched by name **or** by that standard location;
`latex2mathml` is pinned to the last release that ships its license; and
`scripts/packaging/audit_notices.py` checks every pinned package against the
same rule, from any machine, without installing anything.

**Evidence:** the next Mac build carried 124 notice files across 60 packages.

## 8. Legal documents describing the wrong product

**Looked like:** every installer carrying its license, notices and audit.

**Actually:** those documents were written before the `pdf` profile existed,
and said the release *must exclude Docling*. The `pdf` app bundles Docling.

**Found by:** the owner asking to re-confirm the licensing before making the
repository public.

**Fix:** both profiles described as they ship. Reading PDFium's component
licenses as shipped also turned up two that require a statement in the
distribution documentation — FreeType's and the Independent JPEG Group's — and
neither had been made.

## 9. An empty conversion returned as a success

**Looked like:** a guard that refuses a conversion with no text.

**Actually:** it ran only in the `pdf` app, and recognised only one engine's
warning. In a full install, a PDF that was one picture returned **200 and a
97-byte file holding `<!-- image -->`**. An empty `.md` returned **200 and 0
bytes**.

**Found by:** the owner asking *"what does a user get if they upload a picture
with no text?"* — answered by testing every path, not by reading the code that
was meant to handle it.

**Fix:** the question is now asked of the result, in every release and for every
engine: `ConversionResult.has_recovered_text()`. The reason it gives names only
causes that release could have — an app that accepts only Markdown and text does
not blame a scan it cannot receive.

## 10. One file, two sizes

**Looked like:** a page showing each file's size beside a stated limit of 24 MiB.

**Actually:** the page divided by 1,048,576 and labelled the result "MB". Finder
divides by 1,000,000. A file Finder lists as 25.2 MB appeared as 24.0 MB — and
most readers do not know what a MiB is.

**Found by:** the owner asking *"why MiB — isn't it MB?"*

**Fix:** every limit states both, from one constant — **24 MiB（約 25 MB）** — and
the page shows sizes as Finder does.

---

## The pattern

Not one of these was found by a check reporting failure. They were found by
questioning checks that reported success. Five questions found all ten:

1. **How much did it actually look at?** Count the commits, files, bytes or
   seconds. A scan that took 0.05 s read nothing.
2. **Would it pass on a clean machine?** Anything that depends on what happens to
   be installed, or on an untracked file, is luck.
3. **Is "skipped" being counted as "passed"?**
4. **Does the guard cover every path, or only the one it was written for?**
5. **Does the documentation describe what ships, or what was planned?**

And one habit behind all five: **try the case the user will actually hit** — a
real Mac, a real document, a picture with no text in it — rather than the case
the code was written to handle.
