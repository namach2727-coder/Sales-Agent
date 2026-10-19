"""Offline validation of TelBot-only Neon UAT branch host allowlist."""
import unittest

from experiments.telegram_bot_builder.api import is_uat_host


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


if __name__ == "__main__":
    unittest.main()
