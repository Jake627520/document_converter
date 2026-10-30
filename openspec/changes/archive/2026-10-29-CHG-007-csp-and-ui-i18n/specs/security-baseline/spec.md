## ADDED Requirements

### Requirement: Send a restrictive Content-Security-Policy and companion headers from the workbench
The local workbench MUST send the page and every conversion response with `Content-Security-Policy` set to `CSP_DIRECTIVES`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY` and `Referrer-Policy: no-referrer`. The policy MUST be `default-src 'none'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self'; font-src 'self'; object-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'; frame-src 'self' blob: data:;`. Because the page's script and style are inline, `'unsafe-inline'` is a known limitation of this policy, not a guarantee against injected inline script.

#### Scenario: The page is loaded
- **WHEN** the workbench page is requested
- **THEN** the response carries the policy, `nosniff`, `DENY` and `no-referrer`

#### Scenario: A conversion is returned
- **WHEN** a conversion succeeds
- **THEN** the download response carries the policy, `nosniff` and `DENY`

### Requirement: Preview converted HTML only inside a sandbox without scripts
The workbench page MUST show converted HTML inside an `<iframe>` with a `sandbox` attribute that does not grant `allow-scripts`, so that markup in a converted document cannot run script in the workbench. The preview MUST offer a copy control for its content.

#### Scenario: The page is served
- **WHEN** the workbench page is requested
- **THEN** it holds a sandboxed `<iframe>`, the text `allow-scripts` appears nowhere in the page, and a `copy-preview` control is present
