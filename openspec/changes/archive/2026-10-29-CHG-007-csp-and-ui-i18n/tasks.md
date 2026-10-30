# Tasks: CHG-007 CSP Hardening and UI Internationalization

## Phase 1A: CSP and Security Boundaries
- [x] Add security headers constants and middleware injection in `document_converter/web_security.py` and `document_converter/web_app.py`.
- [x] Add sandboxed preview iframe (`sandbox=""`) and copy controls to `PAGE` template in `document_converter/web_app.py`.
- [x] Add regression tests in `tests/test_web_security.py` and `tests/test_web_app.py` for CSP headers, frame-ancestors, preview sandbox attribute, and script isolation.

## Phase 1B: UI Internationalization
- [x] Define comprehensive translation dictionaries for `en`, `zh-TW`, and `zh-CN` (37 keys each) covering all UI labels, hints, messages, and profile descriptions.
- [x] Implement client-side language selector, browser detection, normalization, persistence in `localStorage` (with error handling for unavailable storage), and state-preserving re-rendering.
- [x] Implement server-side error message localization matching client language negotiation, with default fallback to `zh-TW`.
- [x] Add tests for language detection, normalization, fallback, persistence, translation key parity, and localized server responses.

