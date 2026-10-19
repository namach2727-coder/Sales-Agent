"""Offline-only manual BotFather onboarding regression tests.

All credentials synthetic; never access Telegram or Neon.
"""
from __future__ import annotations

import os
import unittest
from unittest.mock import patch
from uuid import UUID

import httpx
from cryptography.fernet import Fernet
from fastapi import HTTPException
from fastapi.testclient import TestClient

from experiments.telegram_bot_builder.api import app
from experiments.telegram_bot_builder.manual_connect import manual_connect, verified_identity
from experiments.telegram_bot_builder.vault import TokenVault


TOKEN = "123456789:" + "Z" * 36
OWNER = 95123
TENANT = UUID("11111111-1111-4111-8111-111111111111")
BOT_UUID = UUID("22222222-2222-4222-8222-222222222222")


def telegram_response(req: httpx.Request) -> httpx.Response:
    assert req.method == "GET" and req.url.host == "api.telegram.org"
    assert req.url.path.endswith("/getMe")
    return httpx.Response(200, json={
        "ok": True, "result": {"id": 7777777, "username": "FakeShopBot", "is_bot": True,
                               "first_name": "Fake Shop"}
    })


class Cursor:
    def __init__(self, row):
        self.row = row
    def fetchone(self):
        return self.row


class MemoryDB:
    def __init__(self, duplicate=False):
        self.duplicate = duplicate
        self.commands = []
        self.commits = 0
        self.rollbacks = 0
    def execute(self, statement, args=()):
        self.commands.append((statement, args))
        if "INSERT INTO telbot.bots" in statement:
            return Cursor(None if self.duplicate else {"id": BOT_UUID})
        return Cursor(None)
    def commit(self):
        self.commits += 1
    def rollback(self):
        self.rollbacks += 1


class ManualConnectTests(unittest.IsolatedAsyncioTestCase):
    async def test_success_encrypts_and_returns_no_credential(self):
        db = MemoryDB()
        key = Fernet.generate_key().decode("ascii")
        result = await manual_connect(
            db=db, tenant_id=TENANT, owner_telegram_user_id=OWNER,
            token=TOKEN, encryption_key=key,
            transport=httpx.MockTransport(telegram_response),
        )
        self.assertEqual(result["username"], "FakeShopBot")
        self.assertEqual(result["status"], "pending")
        self.assertFalse(result["webhook_registered"])
        self.assertFalse(result["message_sending_enabled"])
        self.assertNotIn(TOKEN, repr(result))
        insert = next(item for item in db.commands if "INSERT INTO telbot.bots" in item[0])
        self.assertEqual(insert[1][0], TENANT)
        self.assertEqual(insert[1][1], 7777777)
        self.assertEqual(insert[1][4], OWNER)
        cipher = insert[1][5]
        self.assertIsInstance(cipher, bytes)
        self.assertNotIn(TOKEN.encode(), cipher)
        self.assertEqual(TokenVault(key).decrypt(cipher), TOKEN)
        self.assertEqual(db.commits, 1)
        self.assertEqual(len([s for s, _ in db.commands if "telbot.audit_events" in s]), 1)
        self.assertNotIn(TOKEN, repr(db.commands))

    async def test_same_bot_cannot_connect_to_two_tenants(self):
        db = MemoryDB(duplicate=True)
        with self.assertRaises(HTTPException) as thrown:
            await manual_connect(
                db=db, tenant_id=TENANT, owner_telegram_user_id=OWNER,
                token=TOKEN, encryption_key=Fernet.generate_key().decode("ascii"),
                transport=httpx.MockTransport(telegram_response))
        self.assertEqual(thrown.exception.status_code, 409)
        self.assertEqual(thrown.exception.detail, "Bot already connected")
        self.assertEqual(db.commits, 0)
        self.assertEqual(db.rollbacks, 1)

    async def test_invalid_format_no_outbound(self):
        outgoing = []
        def fail(req):
            outgoing.append(req)
            return telegram_response(req)
        with self.assertRaises(HTTPException) as thrown:
            await verified_identity("not_a_token", transport=httpx.MockTransport(fail))
        self.assertEqual(thrown.exception.status_code, 422)
        self.assertEqual(outgoing, [])

    async def test_bad_credentials_are_sanitized(self):
        transport = httpx.MockTransport(lambda _: httpx.Response(
            401, json={"ok": False, "description": "SECRET VALUE SHOULD NEVER LEAK"}))
        with self.assertRaises(HTTPException) as thrown:
            await verified_identity(TOKEN, transport=transport)
        self.assertEqual(thrown.exception.detail, "Telegram bot token rejected")
        self.assertNotIn(TOKEN, str(thrown.exception))

    async def test_transient_errors_do_not_leak_request_url(self):
        def fail(req):
            raise httpx.ConnectError("Bad URL " + str(req.url), request=req)
        with self.assertRaises(HTTPException) as thrown:
            await verified_identity(TOKEN, transport=httpx.MockTransport(fail))
        self.assertEqual(thrown.exception.status_code, 503)
        self.assertNotIn(TOKEN, str(thrown.exception))


class ManualEndpointGuardTests(unittest.TestCase):
    def test_gate_is_off_by_default_even_without_credentials(self):
        with patch.dict(os.environ, {"TELBOT_ENV": "uat"}, clear=True):
            response = TestClient(app).post(
                f"/api/v1/tenants/{TENANT}/bots/connect-manual",
                json={"bot_token": TOKEN},
            )
        # FastAPI authorization should also reject a missing Mini App signature.
        self.assertIn(response.status_code, (401, 404))

    def test_no_bypass_outside_uat(self):
        with patch.dict(os.environ, {
            "TELBOT_ENV": "prod",
            "TELBOT_MANUAL_CONNECT_ENABLED": "enabled",
            "TELBOT_MANAGER_TOKEN": "111:FAKE",
        }, clear=True):
            response = TestClient(app).post(
                f"/api/v1/tenants/{TENANT}/bots/connect-manual",
                json={"bot_token": TOKEN},
            )
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
