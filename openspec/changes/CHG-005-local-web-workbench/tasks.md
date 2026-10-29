# Tasks: Local Web Workbench

- [x] Add tests for host/request/file/target validation, mocked success, conversion failure and temporary cleanup, and accessible UI controls.
- [x] Implement bounded upload middleware and local Host validation.
- [x] Implement request-scoped conversion and safe download response.
- [x] Build responsive accessible upload workspace with local CSS/JS.
- [x] Add optional web dependencies and loopback-only CLI launcher.
- [x] Document setup, startup, input formats, and local processing limitations.
- [x] Run focused and existing tests, CLI help, and ASGI GET/POST checks where dependencies permit. (2026-10-29: `scripts/local-ci.sh --all` passed, 230 tests with none skipped; `tests/test_web_app.py` drives GET/POST through TestClient; `document-converter web --help` OK.)
