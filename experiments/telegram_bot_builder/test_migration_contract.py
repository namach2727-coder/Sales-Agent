"""Static offline checks complementing the real rollback-only Neon UAT SQL smoke.

Run with python -m unittest discover -s experiments/telegram_bot_builder.
No database credentials or live API calls.
"""
from pathlib import Path
import re
import unittest


MIGRATIONS = Path(__file__).with_name("migrations")
FOUNDATION = MIGRATIONS / "0001_telbot_foundation.sql"
SMOKE = MIGRATIONS / "0001_telbot_uat_smoke_rollback.sql"


class MigrationContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql = FOUNDATION.read_text(encoding="utf-8")
        cls.smoke = SMOKE.read_text(encoding="utf-8")

    def test_target_is_explicit_uat_database(self):
        self.assertIn("br-tiny-poetry-arz49v2o", self.sql)
        self.assertIn("current_database() <> 'telbot'", self.sql)
        self.assertIn("Never execute on production branch", self.sql)

    def test_foundation_has_all_13_tables(self):
        actual = re.findall(r"CREATE TABLE telbot\.([a-z_]+)\s*\(", self.sql)
        self.assertEqual(set(actual), {
            "schema_migrations", "tenants", "tenant_users", "managed_bot_requests",
            "bots", "configuration_versions", "menu_buttons", "reply_rules",
            "faq_entries", "chat_sessions", "inbound_updates",
            "outbound_messages", "audit_events",
        })
        self.assertEqual(len(actual), 13)

    def test_security_and_idempotency_guards_present(self):
        for snippet in (
            "UNIQUE (bot_id,telegram_update_id)",
            "configuration_one_published_per_bot",
            "FOREIGN KEY (tenant_id,configuration_id)",
            "FOREIGN KEY (tenant_id,bot_id)",
            "credential_ciphertext bytea",
            "status <> 'active' OR credential_ciphertext IS NOT NULL",
            "CHECK (jsonb_typeof(metadata) = 'object')",
        ):
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, self.sql)

    def test_migration_is_additive_and_versioned(self):
        self.assertRegex(self.sql, r"(?i)CREATE\s+SCHEMA\s+IF\s+NOT\s+EXISTS")
        self.assertIn("'0001_telbot_foundation'", self.sql)
        self.assertNotRegex(self.sql, r"(?i)\b(DROP|TRUNCATE|DELETE)\s+(?:TABLE|SCHEMA|FROM)\b")
        self.assertEqual(self.sql.count("-- @@statement "), 23)

    def test_uat_smoke_rolls_back_fixture_rows(self):
        self.assertIn("__TELBOT_TEST_ROLLBACK__", self.smoke)
        self.assertIn("EXCEPTION WHEN raise_exception THEN", self.smoke)
        for marker in ("unique_violation", "foreign_key_violation", "check_violation"):
            self.assertIn(marker, self.smoke)


if __name__ == "__main__":
    unittest.main()
