# Design: Local Web Workbench

## Request flow

`POST /convert` validates the local Host and request byte cap, validates the selected output format and upload suffix, writes the upload to a generated path inside `TemporaryDirectory`, invokes `convert_one`, serializes with `write_result`, reads the selected output, then exits the temporary-directory context before returning the bytes. Each request is isolated and nothing is persisted.

## Limits and trust boundaries

- The launcher binds to `127.0.0.1` and exposes only the local UI.
- Host allowlist is `localhost`, `127.0.0.1`, and `::1`; ports are parsed separately. Other hosts receive 400.
- POST requests reject `Sec-Fetch-Site: cross-site`; a supplied Origin must use HTTP and match the Host and port. Loopback aliases are accepted on the same port. Missing Origin is allowed for non-browser clients.
- Request body maximum is 25 MiB; each file is capped at 24 MiB to leave room for multipart framing. Limit file count to five and client-side aggregate selection to 24 MiB. Middleware counts ASGI chunks without retaining or copying the request body; the multipart parser consumes and spools the stream.
- At most two HTTP requests may be active concurrently. Excess requests receive 429 before body consumption. This bounds concurrent conversions, while parser/model/output memory remains engine-dependent.
- Suffix allowlist is derived from pipeline `SUPPORTED`; suffix is normalized lowercase and assigned to a random generated temporary basename. The browser-provided name is display-only.
- Output target allowlist is exactly `md` and `html`.
- Temporary storage is request-scoped and cleanup is guaranteed through a context manager, including conversion exceptions.
- The website selects only `auto` through existing pipeline behavior; optional engines are not installed or enabled by this feature.
- Local upload handling does not imply zero network egress. Engine/model behavior remains dependent on the selected engine and its configuration.

## UI

One responsive page with a dark ink header and warm neutral canvas, a centered work area, a large keyboard-operable file drop zone, visible file rows, output format cards, privacy/local-processing note, submit button, and status region. Use semantic labels, focus-visible outlines, live status announcements, and reduced-motion support. No remote fonts, scripts, stylesheets, or analytics.

## Dependencies and entrypoint

Add FastAPI, Uvicorn, and python-multipart to optional `web` extra. Add `document-converter web --port 8765`; the command imports web dependencies lazily and always binds to `127.0.0.1`.
