"""Safe offline end-to-end tests of UAT self-service and manual bot connection.

No Telegram network requests, no Neon access, and no real bot token.
"""
from __future__ import annotations

import os
import unittest
from unittest.mock import AsyncMock, patch

from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

from experiments.telegram_bot_builder.api import app, get_connection
from experiments.telegram_bot_builder.test_api import Cursor, FakeDB, MANAGER_TOKEN, TENANT_A, BOT_A
from experiments.telegram_bot_builder.test_security import signed_initdata


TOKEN = "123456789:" + "x" * 35


class SelfServiceDb(FakeDB):
    def __init__(self):
        super().__init__()
        self.my_tenant = None
        self.saved_ciphertext = None
        self.audit_logged = False

    def execute(self, query, args=()):
        sql = " ".join(query.split())
        self.commands.append((sql, tuple(args)))
        if "SELECT t.id,t.display_name,tu.role" in sql:
            return Cursor(rows=[] if not self.my_tenant else [self.my_tenant])
        if "SELECT tu.tenant_id FROM telbot.tenant_users tu" in sql:
            return Cursor(None if not self.my_tenant else {"tenant_id": self.my_tenant["id"]})
        if "INSERT INTO telbot.tenants" in sql:
            self.my_tenant = {"id": TENANT_A, "display_name": args[0], "role": "owner"}
            return Cursor(self.my_tenant)
        if "INSERT INTO telbot.tenant_users" in sql:
            return Cursor(None)
        if "INSERT INTO telbot.bots" in sql:
            self.saved_ciphertext = args[-1]
            return Cursor({"id": BOT_A, "username": args[2], "status": "pending"})
        if "INSERT INTO telbot.audit_events" in sql:
            self.audit_logged = True
            return Cursor(None)
        return super().execute(query, args)


class ManualIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.db = SelfServiceDb()
        app.dependency_overrides[get_connection] = lambda: self.db
        self.client = TestClient(app)
        self.headers = {"X-Telegram-Init-Data": signed_initdata(MANAGER_TOKEN)}
        self.secret_key = Fernet.generate_key().decode("ascii")
        self.env = patch.dict(os.environ, {
            "TELBOT_ENV": "uat", "TELBOT_MANAGER_TOKEN": MANAGER_TOKEN,
            "TELBOT_TOKEN_FERNET_KEY": self.secret_key,
        }, clear=True)
        self.env.start()

    def tearDown(self):
        self.env.stop()
        app.dependency_overrides.clear()
        self.client.close()

    def test_owner_can_bootstrap_one_tenant_then_list(self):
        url = "/api/v1/me/tenants"
        new = self.client.post(url, json={"display_name": "  My Business  "}, headers=self.headers)
        self.assertEqual(new.status_code, 201, new.text)
        self.assertEqual(new.json()["display_name"], "My Business")
        self.assertEqual(self.client.get(url, headers=self.headers).json()[0]["role"], "owner")
        duplicate = self.client.post(url, json={"display_name": "Other"}, headers=self.headers)
        self.assertEqual(duplicate.status_code, 409)

    def test_manual_connection_seals_token_and_never_activates(self):
        fake = AsyncMock(return_value={"telegram_bot_id": 7722, "username": "TestCustomerBot", "display_name": "Test"})
        path = f"/api/v1/tenants/{TENANT_A}/bots/connect-manual"
        with patch("experiments.telegram_bot_builder.manual_onboarding.validate_botfather_token", fake):
            response = self.client.post(path, headers=self.headers, json={"bot_token": TOKEN})
        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(response.json()["status"], "pending")
        self.assertEqual(response.json()["username"], "TestCustomerBot")
        self.assertNotIn(TOKEN, response.text)
        self.assertNotIn(TOKEN.encode(), self.db.saved_ciphertext)
        self.assertTrue(self.db.audit_logged)
        self.assertEqual(self.db.commits, 1)
        self.assertEqual(fake.await_count, 1)
        self.assertFalse(any("setWebhook" in query for query, _ in self.db.commands))

    def test_ui_serves_and_does_not_accept_prod_environment(self):
        page = self.client.get("/telbot")
        self.assertEqual(page.status_code, 200)
        self.assertIn("no-store", page.headers.get("cache-control", ""))
        self.assertIn("default-src 'none'", page.headers.get("content-security-policy", ""))
        self.assertIn('dir="rtl"', page.text)
        self.assertIn('id="managed-bot-form"', page.text)
        self.assertIn('id="managed-bot-username"', page.text)
        self.assertIn('id="managed-bot-link"', page.text)
        self.assertNotIn('id="bot-token"', page.text)
        self.assertEqual(self.client.get("/telbot/app.js").status_code, 200)
        with patch.dict(os.environ, {"TELBOT_ENV": "production"}):
            self.assertEqual(self.client.get("/telbot").status_code, 404)


if __name__ == "__main__":
    unittest.main()
