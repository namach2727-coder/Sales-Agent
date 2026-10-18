"""Safe offline API tests: fake database + synthetic Telegram tokens only.

These tests never call Telegram and never access the owner's Neon database.
"""
from __future__ import annotations

import hashlib
import json
import os
import unittest
from unittest.mock import patch
from uuid import UUID

from fastapi.testclient import TestClient
from cryptography.fernet import Fernet

from experiments.telegram_bot_builder.api import app, get_connection
from experiments.telegram_bot_builder.test_security import signed_initdata
from experiments.telegram_bot_builder.vault import TokenVault, CredentialError


TENANT_A = UUID("11111111-1111-4111-8111-111111111111")
TENANT_B = UUID("22222222-2222-4222-8222-222222222222")
BOT_A = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
BOT_B = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")
MANAGER_TOKEN = "111:TESTTOKEN"
MANAGER_WEBHOOK_SECRET = "TEST-Manager-Secret_123"


class Cursor:
    def __init__(self, row=None, rows=None):
        self.row = row
        self.rows = [] if rows is None else rows

    def fetchone(self):
        return self.row

    def fetchall(self):
        return self.rows


class FakeDB:
    """Query facade only; asserts explicit tenant filters through recorded parameters."""

    def __init__(self):
        self.commands = []
        self.manager_updates = set()
        self.inbound_updates = set()
        self.commits = 0
        self.pending_requests = []
        self.registered_bots = {}
        self.receipt_states = []

    def execute(self, query, args=()):
        sql = " ".join(query.split())
        self.commands.append((sql, tuple(args)))
        if "SELECT pg_advisory_xact_lock" in sql:
            return Cursor(None)
        if "FROM telbot.tenant_users tu" in sql and "tu.role='owner'" in sql:
            return Cursor({"role": "owner"}) if args == (TENANT_A, 123456) else Cursor(None)
        if "INSERT INTO telbot.managed_bot_requests" in sql:
            tenant, request_id, user_id = args
            row = {"id": UUID("cccccccc-cccc-4ccc-8ccc-cccccccccccc"),
                   "tenant_id": tenant, "request_id": request_id,
                   "owner_telegram_user_id": user_id, "expires_at": "soon",
                   "status": "pending"}
            if any(x["tenant_id"] == tenant and x["request_id"] == request_id
                   for x in self.pending_requests):
                return Cursor(None)
            self.pending_requests.append(row)
            return Cursor(row)
        if "FROM telbot.managed_bot_requests" in sql and "LIMIT 1" in sql:
            user_id = args[0]
            matches = [row for row in self.pending_requests
                       if row["owner_telegram_user_id"] == user_id
                       and row["status"] == "pending"]
            return Cursor(matches[0] if matches else None)
        if "FROM telbot.managed_bot_requests" in sql and "ORDER BY requested_at DESC" in sql:
            tenant, user_id = args
            return Cursor(rows=[x for x in self.pending_requests
                                if x["tenant_id"] == tenant
                                and x["owner_telegram_user_id"] == user_id])
        if "SELECT r.id,r.tenant_id FROM telbot.managed_bot_requests r" in sql:
            user_id = args[0]
            return Cursor(rows=[x for x in self.pending_requests
                                if x["owner_telegram_user_id"] == user_id
                                and x["status"] == "pending"][:2])
        if "INSERT INTO telbot.bots" in sql:
            tenant, telegram_id, username, display_name, user_id, request_id = args
            if telegram_id in self.registered_bots:
                return Cursor(None)
            self.registered_bots[telegram_id] = {
                "tenant": tenant, "username": username,
                "owner": user_id, "request_id": request_id,
                "status": "pending", "credential_ciphertext": None,
            }
            return Cursor({"id": BOT_A})
        if "UPDATE telbot.managed_bot_requests" in sql:
            request_id, tenant = args
            for item in self.pending_requests:
                if item["id"] == request_id and item["tenant_id"] == tenant:
                    item["status"] = "fulfilled"
            return Cursor(None)
        if "UPDATE telbot.manager_inbound_updates" in sql:
            self.receipt_states.append(args[0])
            return Cursor(None)
        if "FROM telbot.tenant_users tu" in sql:
            tenant, user_id = args
            if user_id == 123456 and tenant == TENANT_A:
                return Cursor({"role": "owner"})
            if user_id == 111222 and tenant == TENANT_A:
                return Cursor({"role": "viewer"})
            return Cursor(None)
        if "SELECT id, telegram_bot_id" in sql and "FROM telbot.bots" in sql:
            tenant = args[0]
            if tenant == TENANT_A:
                return Cursor(rows=[{
                    "id": BOT_A, "telegram_bot_id": 12345, "username": "test_bot",
                    "display_name": "Test Bot", "status": "active", "created_at": None
                }])
            return Cursor(rows=[])
        if "FROM telbot.bots" in sql and "webhook_secret_digest" in sql:
            if args[0] != 12345:
                return Cursor(None)
            return Cursor({"id": BOT_A, "tenant_id": TENANT_A,
                           "webhook_secret_digest": hashlib.sha256(b"child-secret-123").digest()})
        if "SELECT id,telegram_bot_id" in sql and "FROM telbot.bots" in sql:
            tenant, bot_id = args
            return Cursor({"id": BOT_A, "telegram_bot_id": 12345, "username": "test_bot",
                           "display_name": "Test Bot", "status": "active"}) if (
                               tenant == TENANT_A and bot_id == BOT_A
                           ) else Cursor(None)
        if "INSERT INTO telbot.manager_inbound_updates" in sql:
            update_id = args[0]
            if update_id in self.manager_updates:
                return Cursor(None)
            self.manager_updates.add(update_id)
            return Cursor({"id": "manager-event"})
        if "INSERT INTO telbot.inbound_updates" in sql:
            update_id = args[2]
            if update_id in self.inbound_updates:
                return Cursor(None)
            self.inbound_updates.add(update_id)
            return Cursor({"id": "child-event"})
        if "FROM telbot.configuration_versions" in sql:
            return Cursor(None)
        if "SELECT version FROM telbot.schema_migrations" in sql:
            return Cursor({"version": "0002_webhook_auth"})
        raise AssertionError("Unexpected query in isolated test: " + sql[:140])

    def commit(self):
        self.commits += 1


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.db = FakeDB()

        def provide_db():
            yield self.db

        app.dependency_overrides[get_connection] = provide_db
        self.patch = patch.dict(os.environ, {
            "TELBOT_MANAGER_TOKEN": MANAGER_TOKEN,
            "TELBOT_MANAGER_WEBHOOK_SECRET": MANAGER_WEBHOOK_SECRET,
        })
        self.patch.start()
        self.client = TestClient(app, raise_server_exceptions=False)

    def tearDown(self):
        app.dependency_overrides.clear()
        self.patch.stop()
        self.client.close()

    def headers(self, *, user_id=123456):
        return {"X-Telegram-Init-Data": signed_initdata(user_id=user_id)}

    def test_no_unverified_miniapp_read(self):
        result = self.client.get(f"/api/v1/tenants/{TENANT_A}/bots")
        self.assertEqual(result.status_code, 401)

    def test_different_tenant_not_readable(self):
        response = self.client.get(f"/api/v1/tenants/{TENANT_B}/bots", headers=self.headers())
        self.assertEqual(response.status_code, 403)

    def test_owner_sees_only_own_bot_without_token(self):
        result = self.client.get(f"/api/v1/tenants/{TENANT_A}/bots", headers=self.headers())
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual(len(result.json()), 1)
        self.assertNotIn("credential", result.text.lower())
        self.assertNotIn("webhook_secret", result.text.lower())
        self.assertTrue(any(TENANT_A in args for _, args in self.db.commands))

    def test_viewer_cannot_create_draft(self):
        result = self.client.post(
            f"/api/v1/tenants/{TENANT_A}/bots/{BOT_A}/configs",
            json={"greeting": "Hi", "fallback_reply": "Unknown"},
            headers=self.headers(user_id=111222),
        )
        self.assertEqual(result.status_code, 403)

    def test_manager_webhook_secret_required_and_deduplicated(self):
        url = "/api/v1/webhooks/manager"
        payload = {"update_id": 300, "message": {"text": "hello"}}
        denied = self.client.post(url, json=payload)
        self.assertEqual(denied.status_code, 401)
        headers = {"X-Telegram-Bot-Api-Secret-Token": MANAGER_WEBHOOK_SECRET}
        first = self.client.post(url, json=payload, headers=headers)
        second = self.client.post(url, json=payload, headers=headers)
        self.assertEqual(first.status_code, 200, first.text)
        self.assertEqual(first.json(), {"acknowledged": True, "duplicate": False})
        self.assertEqual(second.json(), {"acknowledged": True, "duplicate": True})

    def test_only_tenant_owner_can_request_managed_bot(self):
        route = f"/api/v1/tenants/{TENANT_A}/managed-bot-requests"
        denied = self.client.post(route, json={"suggested_name": "My Store"}, headers=self.headers(user_id=111222))
        self.assertEqual(denied.status_code, 403)
        denied_tenant = self.client.post(
            f"/api/v1/tenants/{TENANT_B}/managed-bot-requests",
            json={"suggested_name": "My Store"}, headers=self.headers(),
        )
        self.assertEqual(denied_tenant.status_code, 403)
        self.assertFalse(self.db.pending_requests)

    def test_create_managed_request_is_only_a_draft_to_deliver(self):
        route = f"/api/v1/tenants/{TENANT_A}/managed-bot-requests"
        result = self.client.post(route, json={"suggested_name": "My Store"}, headers=self.headers())
        self.assertEqual(result.status_code, 201, result.text)
        response = result.json()
        self.assertEqual(response["delivery_status"], "not_sent")
        self.assertGreater(response["request_id"], 0)
        self.assertLess(response["request_id"], 2**31)
        self.assertEqual(response["reply_markup"]["keyboard"][0][0]["request_managed_bot"]["request_id"], response["request_id"])
        self.assertNotIn("token", result.text.lower())
        self.assertEqual(self.db.pending_requests[0]["owner_telegram_user_id"], 123456)
        second = self.client.post(route, json={"suggested_name": "Another"}, headers=self.headers())
        self.assertEqual(second.status_code, 409)

    def test_request_invalid_username_fails_without_persistence(self):
        result = self.client.post(f"/api/v1/tenants/{TENANT_A}/managed-bot-requests",
                                  json={"suggested_name": "Store", "suggested_username": "not a bot"},
                                  headers=self.headers())
        self.assertEqual(result.status_code, 422)
        self.assertEqual(self.db.pending_requests, [])

    def test_verified_manager_event_links_only_one_owner_pending_request(self):
        ticket = {"id": UUID("cccccccc-cccc-4ccc-8ccc-cccccccccccc"),
                  "tenant_id": TENANT_A, "request_id": 123,
                  "owner_telegram_user_id": 123456, "status": "pending"}
        self.db.pending_requests.append(ticket)
        payload = {"update_id": 405, "managed_bot": {
            "user": {"id": 123456}, "bot": {
                "id": 456789, "is_bot": True, "username": "customer_example_bot"}}}
        url = "/api/v1/webhooks/manager"
        headers = {"X-Telegram-Bot-Api-Secret-Token": MANAGER_WEBHOOK_SECRET}
        first = self.client.post(url, json=payload, headers=headers)
        self.assertEqual(first.status_code, 200, first.text)
        self.assertEqual(self.db.registered_bots[456789]["tenant"], TENANT_A)
        self.assertEqual(self.db.registered_bots[456789]["status"], "pending")
        self.assertIsNone(self.db.registered_bots[456789]["credential_ciphertext"])
        self.assertEqual(ticket["status"], "fulfilled")
        self.assertEqual(self.db.receipt_states, ["processed"])
        second = self.client.post(url, json=payload, headers=headers)
        self.assertTrue(second.json()["duplicate"])
        self.assertEqual(len(self.db.registered_bots), 1)

    def test_manager_update_ignores_uninvited_and_ambiguous_owner(self):
        headers = {"X-Telegram-Bot-Api-Secret-Token": MANAGER_WEBHOOK_SECRET}
        url = "/api/v1/webhooks/manager"
        def event(update_id, owner, child):
            return {"update_id": update_id, "managed_bot": {
                "user": {"id": owner}, "bot": {"id": child, "is_bot": True}}}
        uninvited = self.client.post(url, json=event(406, 999999, 88), headers=headers)
        self.assertEqual(uninvited.status_code, 200)
        self.assertFalse(self.db.registered_bots)
        self.db.pending_requests.extend([
            {"id": UUID("cccccccc-cccc-4ccc-8ccc-cccccccccccc"),
             "tenant_id": TENANT_A, "owner_telegram_user_id": 123456,
             "status": "pending"},
            {"id": UUID("dddddddd-dddd-4ddd-8ddd-dddddddddddd"),
             "tenant_id": TENANT_B, "owner_telegram_user_id": 123456,
             "status": "pending"},
        ])
        ambiguous = self.client.post(url, json=event(407, 123456, 89), headers=headers)
        self.assertEqual(ambiguous.status_code, 200)
        self.assertFalse(self.db.registered_bots)
        self.assertEqual(self.db.receipt_states[-1], "ignored")

    def test_child_webhook_invalid_signature_rejected_and_deduplicated(self):
        url = "/api/v1/webhooks/bots/12345"
        body = {"update_id": 301, "message": {"text": "hello"}}
        denied = self.client.post(url, json=body, headers={
            "X-Telegram-Bot-Api-Secret-Token": "wrong-secret"
        })
        self.assertEqual(denied.status_code, 401)
        headers = {"X-Telegram-Bot-Api-Secret-Token": "child-secret-123"}
        first = self.client.post(url, json=body, headers=headers)
        second = self.client.post(url, json=body, headers=headers)
        self.assertEqual(first.status_code, 200, first.text)
        self.assertFalse(first.json()["duplicate"])
        self.assertTrue(second.json()["duplicate"])

    def test_child_webhook_rejects_oversized_payload(self):
        response = self.client.post(
            "/api/v1/webhooks/bots/12345",
            content=json.dumps({"update_id": 1, "padding": "a"*65536}),
            headers={"X-Telegram-Bot-Api-Secret-Token": "child-secret-123",
                     "Content-Type": "application/json"},
        )
        self.assertEqual(response.status_code, 413)

    def test_live_endpoint_only_no_auth(self):
        response = self.client.get("/live")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["service"], "directpilot-telbot-uat")


class VaultTests(unittest.TestCase):
    def test_token_encrypted_and_roundtrips(self):
        vault = TokenVault(Fernet.generate_key().decode("ascii"))
        secret = "123456:synthetic_telegram_token"
        encrypted = vault.encrypt(secret)
        self.assertNotIn(secret.encode(), encrypted)
        self.assertEqual(vault.decrypt(encrypted), secret)
        with self.assertRaises(CredentialError):
            TokenVault(Fernet.generate_key().decode()).decrypt(encrypted)

    def test_missing_or_bad_vault_key_fails_closed(self):
        for value in ("", "not-a-key"):
            with self.assertRaises(CredentialError):
                TokenVault(value)


if __name__ == "__main__":
    unittest.main()
