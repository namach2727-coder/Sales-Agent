"""Offline validation of TelBot-only Neon UAT branch host allowlist."""
import unittest

from experiments.telegram_bot_builder.api import is_uat_host, uat_host_failure_reason


EXPECTED = "ep-wandering-heart-ar7z3k0s-pooler.c-4.us-west-2.aws.neon.tech"
DIRECT = "ep-wandering-heart-ar7z3k0s.c-4.us-west-2.aws.neon.tech"
WRONG_BRANCH = "ep-shiny-lab-arzxdhcd.c-4.us-west-2.aws.neon.tech"


class UatHostGuardTest(unittest.TestCase):
    def test_accepts_the_uat_hosts(self):
        for host in (EXPECTED, DIRECT):
            with self.subTest(host=host):
                self.assertTrue(is_uat_host(f"postgresql://test:fake@{host}/telbot?sslmode=require", EXPECTED))

    def test_rejects_other_neon_branch(self):
        self.assertFalse(is_uat_host(f"postgresql://test:fake@{WRONG_BRANCH}/telbot", EXPECTED))

    def test_rejects_missing_configuration(self):
        self.assertFalse(is_uat_host(f"postgresql://test:fake@{EXPECTED}/telbot", ""))

    def test_rejects_libpq_host_overrides(self):
        for suffix in (f"?host={WRONG_BRANCH}", "?hostaddr=127.0.0.1"):
            with self.subTest(suffix=suffix):
                self.assertFalse(is_uat_host(f"postgresql://test:fake@{EXPECTED}/telbot{suffix}", EXPECTED))

    def test_rejects_bad_schemes_and_spoofed_hosts(self):
        for url in ("sqlite:///telbot", "bad-data", f"postgresql://fake@{EXPECTED}.attack.test/telbot"):
            with self.subTest(url=url):
                self.assertFalse(is_uat_host(url, EXPECTED))


class UatHostReasonTest(unittest.TestCase):
    def test_safe_reason_for_wrong_branch(self):
        wrong = f"postgresql://test:fake@{WRONG_BRANCH}/telbot"
        self.assertEqual(uat_host_failure_reason(wrong, EXPECTED), "hostname_not_in_uat_allowlist")
        self.assertNotIn(WRONG_BRANCH, uat_host_failure_reason(wrong, EXPECTED))

    def test_safe_reason_for_copied_shell_command(self):
        self.assertEqual(
            uat_host_failure_reason(f"psql 'postgresql://user:fake@{DIRECT}/telbot'", EXPECTED),
            "connection_string_format_invalid",
        )

    def test_safe_reason_for_whitespace(self):
        self.assertEqual(
            uat_host_failure_reason(f"postgresql://user:fake@{DIRECT}/telbot ", EXPECTED),
            "connection_string_has_extra_whitespace",
        )

    def test_safe_reason_for_query_host_override(self):
        self.assertEqual(
            uat_host_failure_reason(f"postgresql://user:fake@{DIRECT}/telbot?host=elsewhere", EXPECTED),
            "uri_host_override_disallowed",
        )

    def test_valid_direct_has_no_issue(self):
        self.assertIsNone(uat_host_failure_reason(f"postgresql://test:fake@{DIRECT}/telbot", EXPECTED))



if __name__ == "__main__":
    unittest.main()
