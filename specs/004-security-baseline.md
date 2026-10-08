---
spec_id: "004"
title: "Security, Privacy & Licensing Baseline"
version: "0.2.0"
status: "APPROVED"
updated: "2026-10-08"
---

# 004 - Security, Privacy & Licensing Baseline

## 1. Principles
- **Local-first**: Document processing occurs completely offline. No document payload is sent to cloud AI APIs unless explicitly authorized.
- **Data Leak Prevention**: Converted outputs, temporary assets, `.env`, and model checkpoints are strictly excluded via `.gitignore`.
- **Log Sanitation**: CLI and libraries must not log extracted text contents to console or logfiles.
- **License Isolation**: Marker (GPL-3.0) and MinerU (AGPL-3.0 / CC-BY-NC) must remain optional dependencies.

## 2. CI Verification
Automated checks in `.github/workflows/security-audit.yml`:
1. TruffleHog Secret Scan.
2. `pip-audit` CVE vulnerability scan.
3. `pip-licenses` compliance scan (fail on unauthorized AGPL/GPL packages in core).
