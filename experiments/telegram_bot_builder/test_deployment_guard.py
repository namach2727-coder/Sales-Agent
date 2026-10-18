"""Pure offline UAT DSN metadata tests; no real passwords or Neon access."""
import unittest
from experiments.telegram_bot_builder.deployment_guard import validate_uat_database_url

HOST = "ep-uat-pooler.c-4.us-west-2.aws.neon.tech"
URL = f"postgresql://telbot_ua_runtime:example-placeholder@{HOST}/telbot?sslmode=require"


class DeploymentGuardTests(unittest.TestCase):
    def test_accepted_synthetic_uan_url(self):
        self.assertIsNone(validate_uat_database_url(URL, HOST))

    def test_missing_config_rejected(self):
        for dsn, host in (("", HOST), (URL, ""), (URL, "not-neon.example")):
            with self.subTest(dsn=bool(dsn), host=host), self.assertRaises(ValueError):
                validate_uat_database_url(dsn, host)

    def test_wrong_host_rejected(self):
        with self.assertRaises(ValueError):
            validate_uat_database_url(URL.replace(HOST, "production.neon.tech"), HOST)

    def test_wrong_role_database_rejected(self):
        for changed in (
            URL.replace("telbot_ua_runtime", "telbot_owner"),
            URL.replace("/telbot?", "/neondb?"),
        ):
            with self.assertRaises(ValueError):
                validate_uat_database_url(changed, HOST)

    def test_password_and_tls_required(self):
        for changed in (
            URL.replace(":example-placeholder@", "@"),
            URL.replace("sslmode=require", "sslmode=disable"),
            URL.split("?")[0],
        ):
            with self.assertRaises(ValueError):
                validate_uat_database_url(changed, HOST)

    def test_invalid_port_rejected(self):
        with self.assertRaises(ValueError):
            validate_uat_database_url(URL.replace(HOST, HOST + ":9999"), HOST)


if __name__ == "__main__":
    unittest.main()
