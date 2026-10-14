# Case study: taking an open-source engine to a product you can hand over

This repository converts documents to Markdown, HTML, plain text and Docling JSON
on the user's own computer. The conversion engine is not the interesting part —
it is [Docling](https://github.com/docling-project/docling), MIT-licensed and free
to anyone. What this case study is about is everything between "the engine works
on my machine" and "a colleague can double-click it, and every claim it makes is
true".

## The finding that shaped the project

Ten times, something looked fine and was not.

A secret scan reported success on every push and had read no commit. A
license-notice collector reported success and had silently dropped 21 notices.
A web page returned "200 OK" and a 97-byte file holding nothing. A cleaner
deleted the number `84` from a table and reported the conversion clean.

None of these showed as a failure. Each was found by asking one question of a
check that had passed: **how much did it actually look at?** —
[Chapter 3](03-silent-failures.md) takes them one at a time.

## In numbers

| | |
| --- | --- |
| Pull requests merged | 6 (one more closed as superseded) |
| Defects found and fixed | 10 that looked fine, plus the ones that looked broken |
| Tests | 189 (180 run in CI; 9 need the packaged app's environments) — 2,637 lines of tests against 2,197 lines of product code |
| Coverage | 91% |
| Third-party notices shipped in the macOS app | 124, across 60 packages |
| GPL or AGPL code in the shipped app | none |
| OCR shipped | none, by design — a scan is reported, never guessed at |

## Chapters

1. [Problem and scope](01-problem-and-scope.md) — who it is for, what it
   deliberately does not do, and why not just use MarkItDown
2. [Architecture](02-architecture.md) — one result shape, engines behind
   adapters, release profiles enforced at build time
3. [**Ten things that looked fine**](03-silent-failures.md) — the core of the case study
4. [Verification strategy](04-verification-strategy.md) — what was tested where,
   and what was said plainly to be untested
5. [Licensing and compliance](05-licensing-and-compliance.md) — shipping open
   source inside a proprietary app, and the obligations that come with it
6. [Working with an AI coding agent](06-working-with-an-ai-agent.md) — who
   decided what, and the questions that found the bugs

## How it was built

The code was written by an AI coding agent (Claude Code). The product decisions,
the scope, the risk calls on licensing and publication, and the acceptance on real
hardware with real documents were the project owner's. [Chapter 6](06-working-with-an-ai-agent.md)
is specific about which was which, including where the agent got things wrong.

Every claim here links to the pull request, commit or report that backs it.
