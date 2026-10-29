# Tasks: Document Converter CI Cost Optimization

## 1. Workflow Optimization
- [x] Configure `concurrency` with `cancel-in-progress: true` in `test.yml` and `security-audit.yml`.
- [x] Prevent duplicate push/PR runs on branches.
- [x] Add `paths-ignore` for documentation.
- [x] Add explicit job `timeout-minutes: 15`.
- [x] Add `cache: 'pip'` in `actions/setup-python@v5`.
- [x] Pin TruffleHog action reference.

## 2. Local CI Tooling
- [x] Create executable `scripts/local-ci.sh` supporting `--fast`, `--audit`, `--release`, `--all`.
- [x] Test local CI script under Antigravity.

## 3. License & Documentation
- [x] Review third-party licenses with pip-licenses (verify 0 infectious licenses).
- [x] Ensure proprietary LICENSE is preserved without modification.
- [x] Review and sync `THIRD_PARTY_NOTICES.md`.
