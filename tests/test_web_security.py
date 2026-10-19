"""Dependency-independent security rules for OpenSpec CHG-005."""
from unittest import TestCase

from document_converter.web_security import (
    DOWNLOAD_STEM_LIMIT, RequestAdmission, RequestBodyCounter, RequestBodyTooLarge,
    content_disposition, content_length_exceeds_limit, host_is_local, origin_is_same_local,
    request_exceeds_limit, safe_output_stem, supported_suffix, valid_file_count, valid_target,
    SECURITY_HEADERS, CSP_DIRECTIVES, normalize_locale, SUPPORTED_LOCALES,
)


class WebSecurityTests(TestCase):
    def test_local_host_allowlist_supports_loopback_ports(self):
        for host in ("localhost", "localhost:8765", "127.0.0.1", "127.0.0.1:8765", "[::1]:8765"):
            with self.subTest(host=host):
                self.assertTrue(host_is_local(host))

    def test_external_and_malformed_hosts_are_rejected(self):
        for host in ("evil.example", "localhost.evil.example", "127.0.0.2", "localhost:", "[::1"):
            with self.subTest(host=host):
                self.assertFalse(host_is_local(host))

    def test_origin_must_be_same_local_host_and_port(self):
        self.assertTrue(origin_is_same_local("http://127.0.0.1:8765", "127.0.0.1:8765"))
        self.assertTrue(origin_is_same_local("http://localhost:8765", "127.0.0.1:8765"))
        self.assertFalse(origin_is_same_local("https://127.0.0.1:8765", "127.0.0.1:8765"))
        self.assertFalse(origin_is_same_local("http://localhost:8766", "127.0.0.1:8765"))
        self.assertFalse(origin_is_same_local("http://attacker.example", "127.0.0.1:8765"))

    def test_suffix_validation_is_case_insensitive_and_allowlisted(self):
        self.assertEqual(supported_suffix("notes.MD"), ".md")
        self.assertEqual(supported_suffix("scan.PDF"), ".pdf")
        self.assertIsNone(supported_suffix("payload.exe"))
        self.assertIsNone(supported_suffix("no-extension"))

    def test_output_target_and_file_count_are_bounded(self):
        for target in ("md", "html", "json", "txt"):
            with self.subTest(target=target):
                self.assertTrue(valid_target(target))
        for target in ("docx", "pdf", "", "MD", "../md"):
            with self.subTest(target=target):
                self.assertFalse(valid_target(target))
        self.assertTrue(valid_file_count(1))
        self.assertTrue(valid_file_count(5))
        self.assertFalse(valid_file_count(6))
        self.assertFalse(valid_file_count(0))

    def test_request_limit_rejects_only_values_over_the_cap(self):
        self.assertFalse(request_exceeds_limit(25, 25))
        self.assertTrue(request_exceeds_limit(26, 25))

    def test_active_request_cap_rejects_overflow_and_releases_capacity(self):
        admission = RequestAdmission(limit=2)
        self.assertTrue(admission.try_enter())
        self.assertTrue(admission.try_enter())
        self.assertFalse(admission.try_enter())
        self.assertEqual(admission.active, 2)
        admission.leave()
        self.assertTrue(admission.try_enter())
        admission.leave()
        admission.leave()
        self.assertEqual(admission.active, 0)

    def test_content_length_is_rejected_before_body_read(self):
        self.assertFalse(content_length_exceeds_limit(None, 10))
        self.assertFalse(content_length_exceeds_limit("10", 10))
        self.assertTrue(content_length_exceeds_limit("11", 10))
        self.assertTrue(content_length_exceeds_limit("-1", 10))

    def test_streamed_body_counter_accounts_chunks_without_aggregation(self):
        counter = RequestBodyCounter(limit=5)
        counter.account(2)
        counter.account(3)
        self.assertEqual(counter.received, 5)
        with self.assertRaises(RequestBodyTooLarge):
            counter.account(1)
        self.assertEqual(counter.received, 5)


class DownloadNameTests(TestCase):
    """Deriving a download name from an upload name that is not to be trusted."""

    def test_only_the_last_segment_without_its_suffix_is_kept(self):
        for uploaded, expected in (
            ("resume-1.pdf", "resume-1"),
            ("../../private name.md", "private name"),
            ("C:\\Users\\x\\spec.md", "spec"),
            ("車燈規格表_v3.pdf", "車燈規格表_v3"),
            ("spec.tar.gz", "spec.tar"),
            ("noext", "noext"),
        ):
            with self.subTest(uploaded=uploaded):
                self.assertEqual(safe_output_stem(uploaded), expected)

    def test_a_name_with_nothing_usable_left_falls_back(self):
        for uploaded in ("", ".md", "/.md", "...md", '".md', "   ", "../", "-.md"):
            with self.subTest(uploaded=uploaded):
                self.assertEqual(safe_output_stem(uploaded), "document")

    def test_characters_that_could_change_a_header_or_a_path_are_replaced(self):
        stem = safe_output_stem('a"; filename="evil\r\nSet-Cookie: x=1.md')
        for dangerous in ('"', ";", "\r", "\n", ":", "/", "\\"):
            self.assertNotIn(dangerous, stem)

    def test_a_very_long_name_is_capped(self):
        stem = safe_output_stem("x" * 500 + ".md")
        self.assertEqual(stem, "x" * DOWNLOAD_STEM_LIMIT)

    def test_header_structure_cannot_be_subverted_by_the_name(self):
        stem = safe_output_stem('a"; attachment; filename="evil\r\nSet-Cookie: x=1.md')
        header = content_disposition(stem, "md")
        quoted = header.split('filename="', 1)[1].split('"', 1)[0]
        # The value ends where the quote says it does, and carries no second
        # parameter and no header break of its own.
        self.assertEqual(quoted, f"{stem}.md")
        self.assertNotIn(";", quoted)
        self.assertEqual(header.count("attachment; filename="), 1)
        for dangerous in ("\r", "\n"):
            self.assertNotIn(dangerous, header)

    def test_non_ascii_name_travels_encoded_with_an_ascii_fallback(self):
        header = content_disposition("車燈規格表", "md")
        self.assertIn("filename*=UTF-8''%E8%BB%8A%E7%87%88%E8%A6%8F%E6%A0%BC%E8%A1%A8.md", header)
        self.assertIn('filename="converted-document.md"', header)
        self.assertTrue(header.split('filename="', 1)[1].split('"', 1)[0].isascii())


class CspAndI18nSecurityTests(TestCase):
    def test_security_headers_contain_required_policies(self):
        self.assertIn("Content-Security-Policy", SECURITY_HEADERS)
        self.assertEqual(SECURITY_HEADERS.get("X-Content-Type-Options"), "nosniff")
        self.assertEqual(SECURITY_HEADERS.get("X-Frame-Options"), "DENY")
        self.assertEqual(SECURITY_HEADERS.get("Referrer-Policy"), "no-referrer")

    def test_csp_directives_are_strict_and_comprehensive(self):
        csp = CSP_DIRECTIVES
        self.assertIn("default-src 'none'", csp)
        self.assertIn("script-src 'self' 'unsafe-inline'", csp)
        self.assertIn("style-src 'self' 'unsafe-inline'", csp)
        self.assertIn("img-src 'self' data: blob:", csp)
        self.assertIn("connect-src 'self'", csp)
        self.assertIn("font-src 'self'", csp)
        self.assertIn("object-src 'none'", csp)
        self.assertIn("base-uri 'none'", csp)
        self.assertIn("form-action 'self'", csp)
        self.assertIn("frame-ancestors 'none'", csp)
        self.assertIn("frame-src 'self' blob: data:", csp)

    def test_locale_normalization_and_fallback(self):
        self.assertEqual(SUPPORTED_LOCALES, {"en", "zh-TW", "zh-CN"})
        self.assertEqual(normalize_locale("zh-TW"), "zh-TW")
        self.assertEqual(normalize_locale("zh-HK"), "zh-TW")
        self.assertEqual(normalize_locale("zh-MO"), "zh-TW")
        self.assertEqual(normalize_locale("zh-Hant"), "zh-TW")
        self.assertEqual(normalize_locale("zh-CN"), "zh-CN")
        self.assertEqual(normalize_locale("zh-Hans"), "zh-CN")
        self.assertEqual(normalize_locale("zh-SG"), "zh-CN")
        self.assertEqual(normalize_locale("zh"), "zh-CN")
        self.assertEqual(normalize_locale("en"), "en")
        self.assertEqual(normalize_locale("en-US"), "en")
        self.assertEqual(normalize_locale("en-GB"), "en")
        # Unsupported fallback to en
        self.assertEqual(normalize_locale("fr"), "en")
        self.assertEqual(normalize_locale("de-DE"), "en")
        self.assertEqual(normalize_locale("ja"), "en")
        self.assertEqual(normalize_locale(""), "en")
        self.assertEqual(normalize_locale(None), "en")
