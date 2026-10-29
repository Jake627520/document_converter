## ADDED Requirements

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
