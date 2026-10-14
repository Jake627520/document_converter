# 6. Working with an AI agent

The code, tests and documents in this repository were written by an AI coding
agent (Claude Code). The owner did not write code. This chapter is about how
that division worked, where it failed, and what kept the failures from shipping.

## Who did what

| The agent | The owner |
| --- | --- |
| Wrote the code, tests, build scripts and documents | Decided what to build, and what not to |
| Diagnosed failures and proposed fixes | Chose between the options |
| Opened pull requests, one concern each | Decided when each was merged, or asked for changes |
| Ran the test suite, CI checks and the UAT | Built the app on a real Mac and used it on real documents |
| Researched licenses, upstream tools and platform rules | Decided the license, the visibility, and what to pay for |

## Decisions that were the owner's

Each of these had a reasonable alternative. The agent laid the options out; the
owner chose.

- **No PyTorch**, so no layout model and no OCR — a much smaller app that runs
  on any Mac, at the cost of scanned documents ([Chapter 1](01-problem-and-scope.md)).
- **PDF in the Mac app**, as a second release profile, rather than keeping the
  app to text files.
- **Fix all three CI failures** in the first pull request, rather than only the
  one it was opened for.
- **Drop Python 3.10.** The pull request for it was later closed, its change
  having already reached `main` inside another.
- **No Apple Developer account yet** (USD 99 a year): verify on a virtual machine
  instead, and say plainly that the app is unsigned.
- **Make the repository public** under the existing license, as a free tool, after
  researching what similar tools already exist — and flip the switch personally,
  since it cannot be undone.
- **Keep the case study here**, in the public repository, instead of a separate
  showcase repository.
- **Fix the "MiB" wording**, once its reason was explained, rather than keep the
  more precise but less familiar unit.

## Questions that found defects

The owner's questions were often what exposed a problem — not because they were
technical, but because they asked what a user would see.

| Question or action | What it found |
| --- | --- |
| Building the app on the owner's Mac | 21 license notices silently dropped ([#7 in Chapter 3](03-silent-failures.md#7-license-notices-silently-dropped)) |
| Checking a file the owner had converted | `&amp;` in place of `&` — Markdown output was double-escaping HTML entities |
| The README lists outputs the web page doesn't offer? | `.json` and `.txt` existed on the command line only |
| Can you confirm the licensing once more? | The legal documents described a project without PDF support ([#8](03-silent-failures.md#8-legal-documents-describing-the-wrong-product)) |
| What does a user get for an image with no text? | A successful download of an empty file ([#9](03-silent-failures.md#9-an-empty-conversion-returned-as-a-success)) |
| What if they upload a format we don't support? | Error messages in English on a Chinese page, naming nothing |
| Why "MiB" and not "MB"? | The page divided by 1,048,576 and labelled the result MB ([#10](03-silent-failures.md#10-one-file-two-sizes)) |

None of these needed the owner to know how the code worked. Each needed someone
to look at the product from outside it.

## The agent's own mistakes

These were the agent's, and each was caught before it shipped — some by the
agent, more by the owner, all by checking against something real.

| Mistake | Caught by |
| --- | --- |
| Gave the owner a build path missing a `-pdf-` in the folder name | The owner's terminal: no such directory |
| Advised right-click › Open to get past Gatekeeper — Apple removed that in macOS 15 | Checking current Gatekeeper behaviour while preparing the VM procedure |
| Proposed `--skip-editable` to fix the dependency audit, untested; the project was not installed as editable, so it would have done nothing | Reproducing the CI environment before writing the fix |
| Added the `pdf` profile without updating the legal documents | The owner's request to re-check licensing |
| Found the FreeType acknowledgement and missed the IJG one | Reading every shipped license file in full |
| Said a download-naming behaviour was not deliberate; a test's name showed it was a safety choice | Reading the test before changing it |
| Staged an unrelated change into a commit whose message did not describe it | Reviewing the commit; it was split in two |
| Wrote in this case study that the suite ran with "0 skipped" | Reading the CI log ([Chapter 4](04-verification-strategy.md#the-packaged-apps-tests-do-not-run-in-ci)) |

The pattern is the same one as Chapter 3: a claim made from memory, or from one
environment, instead of from the thing itself.

## What kept mistakes from shipping

- **Every change went through a pull request**, one concern each, with CI green
  before merge. The agent merged only when the owner said to.
- **Every fix came with a test that fails without it**
  ([Chapter 4](04-verification-strategy.md#every-regression-test-is-checked-against-the-bug)).
- **Real hardware, real documents.** The owner's Mac build and the owner's own
  files found what no amount of testing in the agent's environment did.
- **Personal data stays out.** The owner's real documents were used to check
  output and never committed; every committed sample is synthetic.
- **Irreversible steps stay with the owner** — making the repository public,
  paying for a certificate, deciding to merge.
- **"Not verified" is a valid answer.** The agent's environment could not reach
  some hosts and had no Mac. Where something was not checked, the documents say
  so rather than implying it was.

## What this suggests for a similar project

An agent can write and test a product of this size. What it cannot supply is
the outside view: a person who uses the thing, on their own machine, with their
own documents, and asks what it is supposed to do. Most of the ten defects in
Chapter 3 were found at that boundary.
