"""Offline security checks for UAT Telegram manager identity read-only diagnostics."""
import os
import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from experiments.telegram_bot_builder.api import app
from experiments.telegram_bot_builder.manager_identity import _cache

TOKEN = "123456789:" + ("a" * 35)

class ManagerIdentityTests(unittest.TestCase):
    def setUp(self):
        _cache.clear()
        self.client = TestClient(app)
    def test_not_public_outside_uat(self):
        with patch.dict(os.environ,{"TELBOT_ENV":"production","TELBOT_MANAGER_TOKEN":TOKEN},clear=True):
            r=self.client.get("/api/v1/uat/manager-identity")
        self.assertEqual(r.status_code,404)
    def test_missing_key_is_safe(self):
        with patch.dict(os.environ,{"TELBOT_ENV":"uat"},clear=True):
            r=self.client.get("/api/v1/uat/manager-identity")
        self.assertEqual(r.json(),{"status":"missing"})
    def test_match_and_cache_without_leaking_token_or_ids(self):
        from experiments.telegram_bot_builder.manual_onboarding import validate_botfather_token
        with patch.dict(os.environ,{"TELBOT_ENV":"uat","TELBOT_MANAGER_TOKEN":TOKEN},clear=True):
            with patch("experiments.telegram_bot_builder.manual_onboarding.validate_botfather_token",
                       new_callable=AsyncMock) as api:
                api.return_value={"telegram_bot_id":999,"username":"MhnPdr_bot","display_name":"Manager"}
                first=self.client.get("/api/v1/uat/manager-identity")
                second=self.client.get("/api/v1/uat/manager-identity")
                self.assertEqual(first.json(),{"status":"match"})
                self.assertEqual(second.json(),{"status":"match"})
                self.assertEqual(api.await_count,1)
                self.assertNotIn(TOKEN,first.text)
                self.assertNotIn("999",first.text)
    def test_mismatch_returned_only_as_category(self):
        with patch.dict(os.environ,{"TELBOT_ENV":"uat","TELBOT_MANAGER_TOKEN":TOKEN},clear=True):
            with patch("experiments.telegram_bot_builder.manual_onboarding.validate_botfather_token",
                       new_callable=AsyncMock) as api:
                api.return_value={"telegram_bot_id":999,"username":"OtherBot"}
                r=self.client.get("/api/v1/uat/manager-identity")
                self.assertEqual(r.json(),{"status":"mismatch"})
                self.assertNotIn("OtherBot",r.text)
    def test_no_exception_leak(self):
        with patch.dict(os.environ,{"TELBOT_ENV":"uat","TELBOT_MANAGER_TOKEN":TOKEN},clear=True):
            with patch("experiments.telegram_bot_builder.manual_onboarding.validate_botfather_token",
                       new_callable=AsyncMock) as api:
                api.side_effect=RuntimeError("https://api.telegram.org/bot"+TOKEN+"/getMe")
                r=self.client.get("/api/v1/uat/manager-identity")
                self.assertEqual(r.json(),{"status":"unavailable"})
                self.assertNotIn(TOKEN,r.text)

if __name__=="__main__":
    unittest.main()
