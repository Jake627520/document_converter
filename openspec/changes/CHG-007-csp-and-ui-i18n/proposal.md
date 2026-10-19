# Change Proposal: CHG-007 CSP Hardening and UI Internationalization

## Problem

1. **Security Policy**: The local browser workbench currently does not serve a `Content-Security-Policy` (CSP) header, nor other defense-in-depth headers such as `X-Frame-Options` and `Referrer-Policy`. When converted HTML is previewed, injecting arbitrary converted HTML into the application DOM would introduce Cross-Site Scripting (XSS) risks.
2. **Localization**: The browser workbench UI is hardcoded in Traditional Chinese (`zh-Hant`), offering no English (`en`) or Simplified Chinese (`zh-CN`) support, no language selector, and no browser language detection or preference persistence.

## Solution

1. **CSP and Security Boundaries**:
   - Enforce a strict, tailored `Content-Security-Policy` header on all workbench responses:
     `default-src 'none'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self'; font-src 'self'; object-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'; frame-src 'self' blob: data:;`
   - Include complementary security headers: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`.
   - Isolate converted HTML preview inside a sandboxed `<iframe>` boundary (`sandbox="allow-same-origin"` or `sandbox=""`) preventing converted document scripts from executing in or accessing the application DOM.
   - Retain safe Blob URL object lifecycle for downloads and previews.
2. **UI Internationalization**:
   - Introduce lightweight, zero-dependency localization dictionaries for `en`, `zh-TW`, and `zh-CN`.
   - Add a visible language selector in the top bar.
   - Detect browser locale on initial visit, normalize tags, and fall back to `en` for unsupported locales.
   - Persist user language choice in `localStorage`.
   - Ensure changing language preserves currently selected files, output options, and displayed results.
   - Provide localized backend error messages matching the client's locale (defaulting to `zh-TW` for backwards compatibility).

## Acceptance Criteria

- All workbench responses include the tailored `Content-Security-Policy` header.
- Converted HTML preview is rendered inside an isolated, sandboxed iframe.
- Users can switch between English, Traditional Chinese, and Simplified Chinese without losing state.
- Unsupported locales fall back gracefully to English.
- All existing tests continue to pass and new security/i18n regression tests pass.
