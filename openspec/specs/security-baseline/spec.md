## Purpose
Record security and privacy controls that can be checked in the repository, while distinguishing them from unverified runtime behavior.

## Requirements

### Requirement: Exclude common sensitive artifacts from version control
The project MUST maintain ignore patterns for common credentials, generated outputs, temporary assets, and model caches. The ignore rules do not imply that previously tracked files are removed.

#### Scenario: New generated output is untracked
- **WHEN** a generated output matches a configured ignore pattern and has not previously been tracked
- **THEN** Git does not include it as a new file by default

### Requirement: Run security and dependency checks in CI
The security workflow MUST invoke secret, vulnerability, and package-license checks for its configured dependency profile.

#### Scenario: Audit workflow runs
- **WHEN** the security workflow executes
- **THEN** its configured scanners run and their results are available for review

### Requirement: Refuse an input in the interface's language and say what works
A refused upload or request MUST be explained in the language of the interface that received it, MUST name what would be accepted instead where that is knowable, and MUST NOT expose a framework's own validation structure or an interpreter error as the explanation.

#### Scenario: An unsupported file is uploaded
- **WHEN** a file this release does not accept is uploaded
- **THEN** it is refused before conversion starts and the message names the suffixes this release does accept

#### Scenario: A text file is not UTF-8
- **WHEN** a text file in another encoding, such as Big5, GBK or UTF-16, is uploaded
- **THEN** the message names the likely encodings and asks for the file to be saved as UTF-8, rather than reporting a decoding error

#### Scenario: A request arrives malformed
- **WHEN** a request reaches the converter with no file, or otherwise fails validation
- **THEN** it is answered with a sentence the reader can act on, not with the framework's validation output

### Requirement: Describe local processing and license status accurately
Project documentation MUST distinguish the local-first design from unverified network behavior, and MUST identify version-specific package, transitive dependency, model, and deployment license review as pending until verified.

#### Scenario: User evaluates sensitive input or distribution
- **WHEN** a user considers an engine configuration or a software/model distribution
- **THEN** documentation directs them to verify the relevant engine settings and exact license artifacts rather than claiming zero network activity or commercial clearance
