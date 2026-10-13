"""Offline safety tests for guarded database transfer; never connect to real DBs."""
from pathlib import Path
import unittest

from tools.production_db_transfer import (
    TransferError, connection_env, restore, EXPECTED_TARGET_HOST,
)


class ProductionTransferGuards(unittest.TestCase):
    def test_source_production_only(self):
        url = "postgresql://operator:password@dpg-example-a.oregon-postgres.render.com/directpilot_production_db?sslmode=require"
        pg = connection_env(url, source=True)
        self.assertEqual(pg["PGDATABASE"], "directpilot_production_db")
        self.assertEqual(pg["PGPASSWORD"], "password")

    def test_deny_unsafe_source(self):
        for url in [
            "postgres://u:p@localhost/directpilot_production_db",
            "postgres://u:p@dpg-example-a.oregon-postgres.render.com/neondb",
            "postgres://u:p@dpg-example-a.oregon-postgres.render.com/directpilot_production_db?sslmode=disable",
        ]:
            with self.subTest(url=url), self.assertRaises(TransferError):
                connection_env(url, source=True)

    def test_allow_only_independent_neon_destination(self):
        good = f"postgres://u:p@{EXPECTED_TARGET_HOST}/neondb?sslmode=require"
        self.assertEqual(connection_env(good, source=False)["PGHOST"], EXPECTED_TARGET_HOST)
        with self.assertRaises(TransferError):
            connection_env("postgres://u:p@ep-uat.c-4.us-west-2.aws.neon.tech/neondb", source=False)
        with self.assertRaises(TransferError):
            connection_env(f"postgres://u:p@{EXPECTED_TARGET_HOST}/other", source=False)

    def test_restore_does_not_run_without_explicit_confirmation(self):
        with self.assertRaises(TransferError):
            restore(Path("nonexistent.dump"), confirm=False)


if __name__ == "__main__":
    unittest.main()
