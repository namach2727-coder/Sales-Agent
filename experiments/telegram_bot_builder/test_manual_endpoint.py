"""Offline endpoint acceptance: tenant ownership, encryption gate, non-disclosure."""
from __future__ import annotations
import os
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from experiments.telegram_bot_builder.api import app, get_connection
from experiments.telegram_bot_builder.test_api import FakeDB, TENANT_A, TENANT_B, MANAGER_TOKEN
from experiments.telegram_bot_builder.test_security import signed_initdata

class ConnectManualTests(unittest.TestCase):
    def setUp(self):
        self.db=FakeDB()
        app.dependency_overrides[get_connection]=lambda: self.db
        self.client=TestClient(app)
    def tearDown(self):
        app.dependency_overrides.clear()

    def test_no_unauthenticated_token_processing(self):
        with patch.dict(os.environ, {"TELBOT_ENV":"uat","TELBOT_MANAGER_TOKEN":MANAGER_TOKEN},clear=True):
            r=self.client.post(f"/api/v1/tenants/{TENANT_A}/bots/connect-manual",json={"bot_token":"123456789:"+"x"*35})
        self.assertEqual(r.status_code,401)

    def test_no_encryption_key_fails_before_telegram(self):
        with patch.dict(os.environ, {"TELBOT_ENV":"uat","TELBOT_MANAGER_TOKEN":MANAGER_TOKEN},clear=True):
            init=signed_initdata(123456, MANAGER_TOKEN)
            r=self.client.post(f"/api/v1/tenants/{TENANT_A}/bots/connect-manual",
                headers={"X-Telegram-Init-Data":init},json={"bot_token":"123456789:"+"x"*35})
        self.assertEqual(r.status_code,503)
        self.assertEqual(r.json()["detail"],"Bot credential encryption unavailable")

    def test_non_owner_rejected(self):
        with patch.dict(os.environ, {"TELBOT_ENV":"uat","TELBOT_MANAGER_TOKEN":MANAGER_TOKEN},clear=True):
            init=signed_initdata(123456, MANAGER_TOKEN)
            r=self.client.post(f"/api/v1/tenants/{TENANT_B}/bots/connect-manual",
                headers={"X-Telegram-Init-Data":init},json={"bot_token":"123456789:"+"x"*35})
        self.assertEqual(r.status_code,403)
    def test_prod_disabled(self):
        with patch.dict(os.environ, {"TELBOT_ENV":"production","TELBOT_MANAGER_TOKEN":MANAGER_TOKEN},clear=True):
            init=signed_initdata(123456, MANAGER_TOKEN)
            r=self.client.post(f"/api/v1/tenants/{TENANT_A}/bots/connect-manual",
                headers={"X-Telegram-Init-Data":init},json={"bot_token":"123456789:"+"x"*35})
        self.assertEqual(r.status_code,404)

if __name__=="__main__":
    unittest.main()
