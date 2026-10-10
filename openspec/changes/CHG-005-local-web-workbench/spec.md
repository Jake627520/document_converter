# Specification: Local Web Workbench

## Requirements

### Requirement: Loopback-only access

The web launcher MUST bind the server to `127.0.0.1`. The application MUST reject requests whose `Host` is not `localhost`, `127.0.0.1`, or `::1` (an optional numeric port is allowed). The implementation MUST reject oversized request bodies before multipart parsing.

The application MUST admit at most two active HTTP requests at a time, including request body streaming and conversion. Additional requests MUST receive HTTP 429 immediately, before the request body is read. The middleware MUST NOT aggregate or duplicate the complete request body in memory; it MUST count streamed chunks and reject requests over 25 MiB. A declared `Content-Length` above the limit MUST be rejected before body consumption.

For POST requests, the application MUST reject `Sec-Fetch-Site: cross-site`. If an `Origin` header is present, it MUST be HTTP and match the local request host and port; `localhost` and loopback IP aliases may interoperate on the same port. Requests without Origin remain allowed for non-browser clients.

#### Scenario: Remote or rebinding host

- **WHEN** a request uses an unapproved Host value
- **THEN** the application returns HTTP 400 without parsing or saving its body.

#### Scenario: Oversized request

- **WHEN** a request body exceeds 25 MiB
- **THEN** the application returns HTTP 413 and does not pass over-limit chunks to the upload handler.

#### Scenario: Active request limit reached

- **WHEN** two requests are already active
- **THEN** a new request receives HTTP 429 without reading or buffering its body.

#### Scenario: Cross-site form submission

- **WHEN** a POST request carries `Sec-Fetch-Site: cross-site` or a foreign Origin
- **THEN** the application returns HTTP 403 before multipart parsing or conversion.

### Requirement: Validated ephemeral uploads

The application MUST accept only input suffixes in `document_converter.pipeline.SUPPORTED`, accept no more than five files, and allow only `md` or `html` output. Client-supplied file names MUST NOT be used as filesystem paths or output download names. Input and output data MUST be placed in a generated per-request temporary directory and removed on both success and failure.

#### Scenario: Unsupported suffix or target

- **WHEN** the upload suffix is unsupported or target is not `md`/`html`
- **THEN** the application rejects the request without invoking the converter.

#### Scenario: Successful conversion

- **WHEN** a valid document is uploaded with a supported target
- **THEN** the existing conversion adapter is invoked, the output is returned as an attachment with a fixed safe name, and temporary files are removed.

#### Scenario: Conversion fails

- **WHEN** the existing adapter raises an error
- **THEN** the application returns a user-safe error and removes the request temporary directory.

### Requirement: Accessible local conversion UI

The browser page MUST provide a file chooser and drag-and-drop area, a visible selected-file list, Markdown and HTML radio choices, a conversion status region announced to assistive technology, and a download action. It MUST explain local upload handling and that parser/model network behavior is engine-dependent.

#### Scenario: User chooses output

- **WHEN** the user opens the home page
- **THEN** they can choose files and select Markdown or HTML using labeled native controls.

### Requirement: Optional engine isolation

The web dependencies MUST be an optional installation extra. The web interface MUST call the existing `auto` conversion API and MUST NOT install or implicitly choose Marker or MinerU.
