# Development Roadmap

## Done and archived

Archived on 2026-10-29 under `openspec/changes/archive/`; their requirements are in `openspec/specs/`.

- **CHG-001 — Standalone offline HTML renderer**: `document_converter/renderer.py`, used by the writer when no engine supplies HTML.
- **CHG-002 — Batch parallel processing**: one worker by default, a hard limit of four, per-file fault isolation, relative-directory preservation, and collision-safe output names.
- **CHG-003 — Watch mode**: standard-library polling, stable-file fingerprints, output-subtree exclusion, and the batch fault isolation.
- **CHG-004 — Image asset output and reference mapping**: nested asset paths stay safe; matching local Markdown/HTML references are rewritten in `referenced` mode.
- **CHG-008 — CJK PDF detection**: CJK text and ToUnicode CMaps count as a text layer; an empty or corrupt PDF is `unknown`, not `scanned`. Already in `openspec/specs/pdf-detection/`, so archived without a spec update.
- **CI cost optimization**: concurrency, `paths-ignore`, timeouts, pip caching and `scripts/local-ci.sh`. Tooling only, archived without a spec update.

PDF text/scanned detection lives in `document_converter/detector.py` and drives engine selection in `document_converter/pipeline.py`. Do not create a new OCR-detection change unless a specific missing behavior is identified.

## Implemented, spec not yet recorded

The behavior ships and is tested, but the change has no spec delta, so it cannot be archived yet.

- **CHG-005 — Local web workbench**: its `spec.md` sits at the change root instead of `specs/<capability>/spec.md`, and lists only `md`/`html` outputs while the code also offers `json` and `txt`. Needs a `web-workbench` spec delta.
- **CHG-007 — CSP and interface languages**: the security headers, the sandboxed preview and the language selector are in no spec. Needs deltas for `security-baseline` and `web-workbench`.

## Waiting on the owner

- **CHG-006 — Private macOS release**: the candidate builds and its release tests pass. Before distribution the owner confirms the rights owner and recipients and installs on a target machine; a fresh-context acceptance review follows.
- **macOS Developer ID signing and notarization — not planned** (owner's decision, 2026-10-29): the app is not distributed through the App Store, and recipients are few, so it stays signed ad hoc. A recipient opens it once through **System Settings › Privacy & Security › Open Anyway**, as the README describes. Revisit if the app is handed to people who cannot do that; it would need an Apple Developer Program membership, a Developer ID Application certificate, hardened runtime, `notarytool` submission and stapling.

## Next

- **Windows verification**: the README states Windows is untested. A minimal Windows test job, or a recorded manual run, should come before any "known to work" list. A GitHub-hosted Windows runner may cost about twice the Linux minutes; check the account's Actions usage before adding one.
