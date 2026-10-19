# Design: CHG-007 CSP Hardening and UI Internationalization

## 1. Content-Security-Policy & Response Security Headers

### Headers
Every HTTP response originating from the local workbench (HTML page, errors, and conversion output) carries:
- `Content-Security-Policy`:
  `default-src 'none'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self'; frame-ancestors 'none'; frame-src 'self' blob: data:; base-uri 'self'; form-action 'self';`
- `X-Content-Type-Options`: `nosniff`
- `X-Frame-Options`: `DENY`
- `Referrer-Policy`: `no-referrer`

### Hardening Limitation & Directive Rationale
- `script-src 'self' 'unsafe-inline'`: **Hardening limitation**. Permits inline scripts because the single-page workbench currently serves all JavaScript logic inline within `PAGE`.
  - *Removal feasibility without rewrite*: The current Python backend dynamically renders `PAGE` via `base_page()`. Generating a cryptographic per-request nonce (e.g. `nonce-{uuid}`) or computing a SHA-256 hash of the inline script block and attaching `script-src 'self' 'nonce-...'` is technically feasible without rewriting the frontend in React/Vite. In Phase 1, `'unsafe-inline'` is retained to avoid breaking dynamic inline handlers until nonce middleware is scheduled.
- `style-src 'self' 'unsafe-inline'`: Permits inline CSS styling for the standalone UI without external network dependencies.
- `img-src 'self' data: blob:`: Allows local icons, SVG data URIs, and blob URIs for generated output images.
- `connect-src 'self'`: Limits `fetch()` to the loopback origin (`/convert`). External telemetry and network requests are strictly forbidden.
- `frame-ancestors 'none'`: Forbids framing the workbench inside any external website, preventing UI redressing / clickjacking.
- `frame-src 'self' blob: data:`: Allows sandboxed preview `<iframe>` loading without granting external frame permissions.

## 2. Preview Isolation Boundary

- Rendered HTML is displayed inside an `<iframe id="preview-frame" sandbox="" class="preview-frame" title="Document Preview">`.
- The `sandbox=""` attribute strictly lacks `allow-scripts`, preventing any converted or user-uploaded HTML scripts, event handlers, or SVG scripts from executing.
- The `sandbox=""` attribute strictly lacks `allow-same-origin`, forcing the preview context into a unique opaque origin (`null`), blocking access to parent DOM, cookies, and `localStorage`.
- Raw text / Markdown / JSON preview is inserted using `element.textContent` in a `<pre><code>` container, guaranteeing that special characters are not treated as markup.
- A "Copy" button uses `navigator.clipboard.writeText(...)` to copy the plain text content.

## 3. UI Internationalization (i18n)

### Locale Representation
- Supported locales: `en` (English), `zh-TW` (Traditional Chinese), `zh-CN` (Simplified Chinese).
- Normalized mapping:
  - `zh-TW`, `zh-HK`, `zh-MO`, `zh-Hant` -> `zh-TW`
  - `zh-CN`, `zh-SG`, `zh-Hans`, `zh` -> `zh-CN`
  - `en*` -> `en`
  - All other language tags fall back to `en`.

### Client State & Persistence
- Storage key: `doc_conv_lang` in `localStorage` (guarded with `try/catch` to handle private browsing and blocked storage gracefully).
- On initial visit: inspect `localStorage.getItem("doc_conv_lang")`; if absent or invalid, inspect `navigator.languages` / `navigator.language`; normalize or fall back to `en`.
- Language selector: `<select id="lang-select">` rendered in `.topbar`.
- Reactive updates: on change, store preference, update all UI strings via a translation lookup table (37 unique keys), update `html[lang]`, and re-render `draw()` without mutating `selected` files or resetting radio choices.
- Server error messages: support client-negotiated language via `Accept-Language` or optional form parameter `lang`, falling back to `zh-TW` if unspecified to preserve complete backward compatibility with existing tests.
