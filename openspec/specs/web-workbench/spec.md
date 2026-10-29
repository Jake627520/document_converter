# web-workbench Specification

## Purpose
Define the local browser workbench (`document-converter web` and the packaged app): who it answers, what it accepts, how it names and returns a conversion, and which language it speaks. Release-specific inputs and outputs are in release-profiles; response headers and the preview sandbox are in security-baseline.

## Requirements

### Requirement: Accept requests only for a loopback host
The workbench MUST refuse any request whose `Host` is not `localhost`, `127.0.0.1` or `::1` (bracketed as `[::1]`), with an optional numeric port, and MUST do so before the request body is parsed. A malformed host, such as `localhost:` or an unclosed `[::1`, MUST be refused as well.

#### Scenario: Remote or rebinding host
- **WHEN** a request arrives with `Host: evil.example`, `localhost.evil.example` or `127.0.0.2`
- **THEN** the workbench answers HTTP 400 without reading the upload

#### Scenario: Loopback host with a port
- **WHEN** a request arrives with `Host: 127.0.0.1:8765`, `localhost:8765` or `[::1]:8765`
- **THEN** the request is processed

### Requirement: Refuse cross-site conversion requests
A POST request MUST be refused with HTTP 403 when it carries `Sec-Fetch-Site: cross-site`, or when it carries an `Origin` that is not an `http` origin on an allowed loopback host with the same port as the `Host`. `localhost` and the loopback addresses MUST be interchangeable on the same port. A POST without an `Origin` MUST NOT be refused on that ground, so that non-browser clients keep working.

#### Scenario: Cross-site form submission
- **WHEN** a POST to `/convert` carries `Sec-Fetch-Site: cross-site` or `Origin: https://attacker.example`
- **THEN** the workbench answers HTTP 403 and does not convert the upload

#### Scenario: Origin on another scheme or port
- **WHEN** the `Origin` is `https://127.0.0.1:8765` or `http://localhost:8766` and the `Host` is `127.0.0.1:8765`
- **THEN** the origin is not accepted as the same local origin

#### Scenario: Loopback alias on the same port
- **WHEN** the `Origin` is `http://localhost:8765` and the `Host` is `127.0.0.1:8765`
- **THEN** the origin is accepted

### Requirement: Bound request size, file size, file count and concurrent work
The workbench MUST admit at most `MAX_ACTIVE_REQUESTS` (2) active requests and MUST refuse a further request before reading its body. It MUST refuse a request whose declared `Content-Length` exceeds `MAX_REQUEST_BYTES` (25 MiB) before reading the body, and MUST count streamed body chunks without aggregating them, refusing with HTTP 413 before forwarding a chunk that would pass the cap. It MUST refuse with HTTP 413 any single file over `MAX_FILE_BYTES` (24 MiB), and with HTTP 400 a request with fewer than 1 or more than `MAX_FILE_COUNT` (5) files. The page MUST check the same 24 MiB limit per file and in total before it sends anything.

#### Scenario: Active request limit reached
- **WHEN** two requests are active and a third arrives
- **THEN** the third is refused, and capacity returns once an active request finishes

#### Scenario: Oversized request body
- **WHEN** a request declares or streams more bytes than the request cap
- **THEN** the workbench answers HTTP 413 and the over-limit chunk is not passed to the upload handler

#### Scenario: Oversized file or too many files
- **WHEN** one file exceeds 24 MiB, or six files are sent
- **THEN** the workbench answers HTTP 413 or HTTP 400 respectively, and the message states the limit

#### Scenario: The page checks the server's limit
- **WHEN** the page is served
- **THEN** its client-side check uses the same byte limit as `MAX_FILE_BYTES` and shows sizes in decimal megabytes

### Requirement: Validate input suffix and output format before converting
The workbench MUST accept only an upload whose final suffix, compared case-insensitively, is in `document_converter.formats.SUPPORTED`, and only an output target in `ALLOWED_TARGETS` (`md`, `html`, `json`, `txt`), compared exactly. Anything else MUST be refused with HTTP 400 before the converter runs. A release profile narrows both sets as the release-profiles capability states, and the wording of the refusal follows security-baseline's "Refuse an input in the interface's language and say what works".

#### Scenario: Unsupported suffix
- **WHEN** `payload.exe` or a file with no suffix is uploaded
- **THEN** the request is refused with HTTP 400

#### Scenario: Suffix in another case
- **WHEN** `notes.MD` or `scan.PDF` is uploaded
- **THEN** the suffix is accepted as `.md` or `.pdf`

#### Scenario: Unknown or malformed target
- **WHEN** the target is `docx`, `pdf`, empty, `MD` or `../md`
- **THEN** the request is refused with HTTP 400

### Requirement: Keep uploads ephemeral and away from client-chosen paths
The workbench MUST write each upload under a generated name (`input-<random hex><suffix>`) inside a per-request temporary directory, MUST NOT use the client-supplied file name as a filesystem path, and MUST remove that directory after the response body is built, whether the conversion succeeded or failed.

#### Scenario: Successful conversion
- **WHEN** an upload named `../../private name.md` converts successfully
- **THEN** the converter sees a generated path that does not contain the uploaded name, the file exists during conversion, and it no longer exists after the response

#### Scenario: Conversion fails
- **WHEN** the converter raises an error
- **THEN** the workbench answers HTTP 422 and the request's temporary directory no longer exists

### Requirement: Name the download after the uploaded document without trusting it
A single converted file MUST be returned as an attachment whose name is the last path segment of the uploaded name with its final suffix dropped, with header-breaking and path characters replaced, capped at `DOWNLOAD_STEM_LIMIT` (120) characters, and replaced by `document` if nothing usable is left. The `Content-Disposition` header MUST carry the real name percent-encoded in `filename*` and MUST put an ASCII name in `filename`, using `converted-document` when the name is not ASCII. Several files MUST be returned as one `converted-documents.zip` whose entries keep their names and do not overwrite each other. The response MUST use the media type of the target, such as `text/plain; charset=utf-8` for `txt` and `application/json; charset=utf-8` for `json`.

#### Scenario: Traversal in the uploaded name
- **WHEN** `../../private name.md` is converted to Markdown
- **THEN** the header is `attachment; filename="private name.md"; filename*=UTF-8''private%20name.md` and holds no `..`, `/`, `\`, CR or LF

#### Scenario: Non-ASCII name
- **WHEN** `車燈規格表_v3.md` is converted
- **THEN** `filename*` carries the percent-encoded UTF-8 name and `filename` is `converted-document.md`

#### Scenario: Several files share a name
- **WHEN** `headlamp.md`, `headlamp.md` and `面板備忘.md` are converted together
- **THEN** the zip holds `headlamp.md`, `headlamp-2.md` and `面板備忘.md`

#### Scenario: Name holds only a suffix
- **WHEN** `.md` is converted
- **THEN** the download is named `document.md`

### Requirement: Provide labelled native upload and output controls
The page MUST provide a native file input with an `accept` list, one native radio input named `target` for each output the running release offers, and a status region with `aria-live="polite"`. Outside a release profile it MUST offer `md`, `html`, `txt` and `json`.

#### Scenario: User opens the page
- **WHEN** the page is requested without a release profile
- **THEN** it holds a `type="file"` input, radio inputs for `md`, `html`, `txt` and `json`, and a polite live status region

### Requirement: Say when the model-free PDF reader ran
When any file in a request was converted by the `docling-native` engine, the response MUST carry `X-Conversion-Notes: model-free`, and the page MUST show a note in the interface's language that the model-free reader does not rebuild heading levels, tables or reading order. Other engines MUST NOT set that header.

#### Scenario: docling-native converts the upload
- **WHEN** the conversion result names the `docling-native` engine
- **THEN** the response carries `X-Conversion-Notes: model-free`

#### Scenario: Another engine converts the upload
- **WHEN** the conversion result names another engine, such as `text_direct`
- **THEN** the response carries no `X-Conversion-Notes` header

### Requirement: Offer the interface in Traditional Chinese, Simplified Chinese and English
The workbench MUST provide its interface in `zh-TW`, `zh-CN` and `en` from one translation table per language, and every language MUST define the same keys. The page MUST carry a language selector (`lang-select`) offering all three, and MUST set `html[lang]`, the selector's label and the preview frame's title in the language it is rendered in.

#### Scenario: The selector lists every language
- **WHEN** the page is requested
- **THEN** `lang-select` offers `zh-TW`, `zh-CN` and `en`

#### Scenario: Translations stay in step
- **WHEN** the three translation tables are compared
- **THEN** they hold exactly the languages `zh-TW`, `zh-CN` and `en`, and each defines the same set of keys

#### Scenario: Attributes follow the language
- **WHEN** the page is rendered in English
- **THEN** the selector is labelled `Language selection` and the preview frame is titled `Document Preview`

### Requirement: Render the page in the language the request asks for
The page MUST be rendered in the language given by the `lang` query parameter when one is present. A language tag MUST be normalized to a supported language: `zh-TW`, `zh-HK`, `zh-MO` and `zh-Hant` to `zh-TW`; `zh-CN`, `zh-SG`, `zh-Hans` and `zh` to `zh-CN`; `en` and `en-*` to `en`; any other tag, or an empty one, to `en`. A request that names no language at all MUST be rendered in `zh-TW`, the language the workbench used before this change.

#### Scenario: Query parameter names a supported language
- **WHEN** the page is requested with `?lang=en`, `?lang=zh-CN` or `?lang=zh-TW`
- **THEN** the page is rendered with that `lang` and that language's text

#### Scenario: Query parameter names an unsupported language
- **WHEN** the page is requested with `?lang=fr-FR`
- **THEN** the page is rendered in English

#### Scenario: No language is named
- **WHEN** the page is requested with no `lang` parameter and no `Accept-Language`
- **THEN** the page is rendered in Traditional Chinese

### Requirement: Answer each request in the language its Accept-Language names
Conversion responses and the loopback, cross-site and size refusals MUST be worded in the language normalized from the first tag of the request's `Accept-Language` header, and MUST be worded in `zh-TW` when the request sends none. This fixes how security-baseline's "Refuse an input in the interface's language and say what works" finds the interface's language.

#### Scenario: English is requested
- **WHEN** a request with `Accept-Language: en-US,en;q=0.9` names an invalid output format
- **THEN** the refusal reads "Please choose an output format"

#### Scenario: Simplified Chinese is requested
- **WHEN** a request with `Accept-Language: zh-CN` uploads an unsupported `.xyz` file or a file over the size limit
- **THEN** the refusal is worded in Simplified Chinese

#### Scenario: A boundary refusal is localized
- **WHEN** a request with `Accept-Language: en` uses a non-loopback host or arrives cross-site
- **THEN** the HTTP 400 or HTTP 403 explanation is in English

#### Scenario: No language is sent
- **WHEN** a request without `Accept-Language` names an invalid output format
- **THEN** the refusal is worded in Traditional Chinese
