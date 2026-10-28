# OpenSpec Proposal: Document Converter CI Cost Optimization & Third-Party Audit

## Context & Problem
`document_converter` is a public repository with two GitHub Actions workflows:
1. `test.yml`: Runs tests across Python 3.11 and 3.12, plus an isolated Linux release-runtime environment.
2. `security-audit.yml`: Runs TruffleHog secret scan, pip-audit, and pip-licenses compliance audit.

Recent 30-day metrics show 99 workflow runs consuming ~266 runner minutes. Key inefficiencies include:
- `push: branches: ["main", "feat/*", "develop"]` and `pull_request: branches: ["main"]` simultaneously trigger duplicate workflow executions when a feature branch with an active PR is pushed.
- Absence of `concurrency` configuration causes stale queued runs to waste minutes when multiple commits are rapidly pushed.
- Documentation updates trigger full Python matrix and security audits unnecessarily.
- Actions lack timeouts (risking 6-hour execution limits if hung) and dependency caching.

## Proposed Changes
1. **GitHub Workflows Optimization**:
   - Add `concurrency` (`group: ${{ github.workflow }}-${{ github.ref }}`, `cancel-in-progress: true`) across both workflows.
   - Refactor triggers to avoid duplicate runs on feature branches targeting PRs.
   - Add `paths-ignore` for markdown and doc files (`docs/**`, `*.md`, `LICENSE`, `THIRD_PARTY_NOTICES.md`).
   - Add explicit `timeout-minutes: 15` per job.
   - Add `cache: 'pip'` to `actions/setup-python@v5`.
   - Pin TruffleHog action version to avoid unexpected upstream `@main` breaking changes.
2. **Local CI Script**:
   - Create `scripts/local-ci.sh` for one-click Antigravity execution (`--fast`, `--audit`, `--release`, `--all`).
3. **Governance & License Compliance**:
   - Retain proprietary LICENSE (Version 1.0 — 2026-10-09).
   - Review and update `THIRD_PARTY_NOTICES.md`.
   - Provide independent evaluation of open-source licensing feasibility.
