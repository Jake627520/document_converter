# 1. Problem and scope

**English** | [繁體中文](01-problem-and-scope.zh-TW.md) | [简体中文](01-problem-and-scope.zh-CN.md)

## The problem

People who work with specifications, internal memos and review documents want
them as Markdown or plain text — for a knowledge base, a wiki, or to hand to an
AI assistant. The documents are often confidential. Uploading them to an online
converter is exactly what they should not do.

So the requirement was simple to state and easy to get wrong: **convert on the
user's own computer, and never send the document anywhere.**

## Who it is for

| User | Needs | What that rules out |
| --- | --- | --- |
| Someone with confidential documents | Nothing leaves the machine | Any cloud API, any telemetry, any model downloaded at run time without saying so |
| A non-technical colleague | Double-click and use it | "First install Python 3.12, then…" |
| A developer | Run it from source, script it | A closed binary with no CLI |

That gave three front ends over one core: a command line, a browser workbench
served only on `127.0.0.1`, and a packaged macOS app.

## Why not just use MarkItDown?

Microsoft's [MarkItDown](https://github.com/microsoft/markitdown) is free,
MIT-licensed and very widely used. On conversion quality alone there is no
winning against it.

But its own contributing guide lists **desktop and web applications as out of
scope**. It is a library and a CLI. The gap it leaves is the one this project
aims at: something a person who has never opened a terminal can use, with every
statement it makes about itself checked.

The engine here is Docling instead, for one specific reason: it offers a
`NativePdfPipeline` that reads the text a PDF already holds **without loading
any AI model**. That made the next decision possible.

## The decision that defined the shipped app: no PyTorch

Docling's default PDF pipeline runs layout and table models. They need PyTorch —
a multi-gigabyte install — and download model weights the first time they run.

For a double-click app meant for confidential documents, both are wrong: the app
becomes enormous, and "downloads weights on first use" is a network call the
user did not ask for. So the owner's call was to **skip PyTorch entirely** and
build on the model-free reader. The cost is real and is stated everywhere it
applies: no heading hierarchy rebuilt, no Markdown tables, no OCR.

## Two release profiles, each with a hard boundary

Rather than one app with every feature, two reviewed profiles:

| Profile | Accepts | Bundles | Why it exists |
| --- | --- | --- | --- |
| `text` | `.md` `.markdown` `.txt` | **No document engine at all** | The smallest thing that is useful — the least code and the fewest licenses to answer for |
| `pdf` | the above, plus PDFs with a text layer | Docling's model-free reader and PDFium | PDF is what people actually have |

A profile is not a setting a user can flip. It is enforced when the app is built:
the build refuses to freeze any module on the profile's forbidden list, and the
frozen app reports at start-up that none was loaded. [Chapter 2](02-architecture.md)
shows how.

## What it deliberately does not do

| Not done | Why |
| --- | --- |
| **OCR** for scanned PDFs | Every OCR option means either a model download or a license with conditions. A scan is reported as having no text layer — never guessed at |
| Office documents and images in the app | They need the model pipeline this app was scoped to avoid |
| **Apple notarization** | It needs a paid Apple Developer account (USD 99 a year). Until the app has users outside the owner's circle, that cost is not justified; [`docs-release/macos-vm-verification.md`](../../docs-release/macos-vm-verification.md) covers clean-machine testing without it |
| Windows | No installer, no testing — and the documentation says so rather than implying otherwise |

Each exclusion is written down where a user would look for the feature. A
missing feature that is documented is a decision; one that is not is a bug
report waiting to happen.
