"""Safe offline API tests: fake database + synthetic Telegram tokens only.

These tests never call Telegram and never access the owner's Neon database.
"""
from __future__ import annotations

import ast
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
        if "SELECT t.id,t.display_name,tu.role FROM telbot.tenant_users tu" in sql:
            return Cursor(rows=[])
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
        if "SELECT request_id FROM telbot.managed_bot_requests" in sql:
            tenant, request_id, owner = args
            matches = [r for r in self.pending_requests if r["tenant_id"] == tenant and r["request_id"] == request_id and r["owner_telegram_user_id"] == owner and r["status"] == "pending"]
            return Cursor(matches[0] if matches else None)
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
        if "SELECT telegram_bot_id,credential_ciphertext FROM telbot.bots" in sql:
            bot_id, tenant_id, user_id = args
            if (bot_id, tenant_id, user_id) == (BOT_A, TENANT_A, 123456):
                return Cursor({"telegram_bot_id": 123456, "credential_ciphertext": getattr(self, "managed_ciphertext", None)})
            return Cursor(None)
        if "UPDATE telbot.bots SET credential_ciphertext" in sql:
            ciphertext, bot_id, tenant_id, user_id = args
            self.managed_ciphertext = ciphertext
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

    def test_standalone_vercel_imports_safe_auth_diagnostic(self):
        """Protect the fallback import path used by /var/task/api.py on Vercel."""
        from pathlib import Path
        module_path = Path(__file__).with_name("api.py")
        tree = ast.parse(module_path.read_text(encoding="utf-8"))
        fallback = [node for node in ast.walk(tree)
                    if isinstance(node, ast.ImportFrom) and node.module == "auth"]
        self.assertEqual(len(fallback), 1)
        names = {alias.name for alias in fallback[0].names}
        self.assertIn("safe_initdata_shape", names)

    def test_no_unverified_miniapp_read(self):
        result = self.client.get(f"/api/v1/tenants/{TENANT_A}/bots")
        self.assertEqual(result.status_code, 401)

    def test_signed_miniapp_with_ed25519_field_is_authorized(self):
        with patch.dict(os.environ, {"TELBOT_ENV": "uat"}):
            response = self.client.get("/api/v1/me/tenants", headers={
                "X-Telegram-Init-Data": signed_initdata(signature=True)
            })
            self.assertEqual(response.status_code, 200)
            self.assertIsInstance(response.json(), list)

    def test_unauthorized_reason_is_safe_and_uat_only(self):
        with patch.dict(os.environ, {"TELBOT_ENV": "uat"}):
            missing = self.client.get("/api/v1/me/tenants")
            self.assertEqual(missing.status_code, 401)
            self.assertEqual(missing.json(), {"detail": "missing_init_data"})
            bad = self.client.get("/api/v1/me/tenants", headers={
                "X-Telegram-Init-Data": signed_initdata(token="999:WRONG")
            })
            self.assertEqual(bad.status_code, 401)
            self.assertEqual(bad.headers.get("X-TelBot-UAT-Auth-Shape"), "q0_c0_s0_u1_a1")
            self.assertEqual(bad.headers.get("X-TelBot-UAT-Ed25519"), "unavailable")
            self.assertEqual(bad.headers.get("X-TelBot-UAT-HMAC-Diag"), "key_or_payload_mismatch")
            self.assertEqual(bad.json(), {"detail": "invalid_signature"})
            self.assertNotIn("WRONG", bad.text)
        with patch.dict(os.environ, {"TELBOT_ENV": "production"}):
            result = self.client.get("/api/v1/me/tenants")
            self.assertEqual(result.json(), {
                "detail": "Invalid Telegram Mini App authentication"
            })
            self.assertNotIn("X-TelBot-UAT-Auth-Shape", result.headers)
            self.assertNotIn("X-TelBot-UAT-Ed25519", result.headers)
            self.assertNotIn("X-TelBot-UAT-HMAC-Diag", result.headers)

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

    def test_prepare_managed_token_is_server_only_and_owner_scoped(self):
        path = f"/api/v1/tenants/{TENANT_A}/bots/{BOT_A}/prepare-managed-credential"
        with patch.dict(os.environ, {"TELBOT_ENV": "uat",
                                     "TELBOT_TOKEN_FERNET_KEY": Fernet.generate_key().decode()}):
            with patch("experiments.telegram_bot_builder.managed_credentials.fetch_managed_bot_token",
                       return_value="123456:ABCDEFGHIJKLMNOPQRSTUVWXYZabc123456") as fetch:
                denied = self.client.post(path, headers=self.headers(user_id=111222))
                self.assertEqual(denied.status_code, 403)
                self.assertEqual(fetch.call_count, 0)
                response = self.client.post(path, headers=self.headers())
                self.assertEqual(response.status_code, 200, response.text)
                self.assertEqual(response.json(), {"status": "credential_stored"})
                self.assertNotIn("ABCDEFGHIJKLMNOPQRSTUVWXYZ", response.text)
                stored = self.db.managed_ciphertext
                self.assertIsInstance(stored, bytes)
                self.assertNotIn(b"ABCDEFGHIJKLMNOPQRSTUVWXYZ", stored)
                again = self.client.post(path, headers=self.headers())
                self.assertEqual(again.status_code, 200)
                self.assertEqual(fetch.call_count, 1)

    def test_native_managed_keyboard_is_owner_only(self):
        import httpx
        route = f"/api/v1/tenants/{TENANT_A}/managed-bot-requests"
        created = self.client.post(route, json={"suggested_name": "Test Bot"}, headers=self.headers())
        request_id = created.json()["request_id"]
        url = route + f"/{request_id}/send-keyboard"
        denied = self.client.post(url, headers=self.headers(user_id=111222))
        self.assertEqual(denied.status_code, 403)
        with patch.dict(os.environ, {"TELBOT_ENV": "uat", "TELBOT_MANAGER_TOKEN": MANAGER_TOKEN}):
            async def answer(request):
                body = json.loads(request.content)
                self.assertEqual(body["chat_id"], 123456)
                self.assertEqual(body["reply_markup"]["keyboard"][0][0]["request_managed_bot"]["request_id"], request_id)
                return httpx.Response(200, json={"ok": True, "result": {"message_id": 3}})
            with patch("httpx.AsyncClient") as factory:
                client = factory.return_value.__aenter__.return_value
                client.post.side_effect = answer
                result = self.client.post(url, headers=self.headers())
                self.assertEqual(result.status_code, 200, result.text)
                self.assertEqual(result.json(), {"status": "sent_in_private_chat"})
                self.assertNotIn(MANAGER_TOKEN, result.text)

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
        self.assertEqual(response["delivery_status"], "user_confirmation_required")
        self.assertTrue(response["creation_url"].startswith("https://t.me/newbot/DirectPilotManagerBot/"))
        self.assertGreater(response["request_id"], 0)
        self.assertLess(response["request_id"], 2**31)
        self.assertEqual(response["reply_markup"]["keyboard"][0][0]["request_managed_bot"]["request_id"], response["request_id"])
        self.assertNotIn("token", result.text.lower())
        self.assertEqual(self.db.pending_requests[0]["owner_telegram_user_id"], 123456)
        second = self.client.post(route, json={"suggested_name": "Another"}, headers=self.headers())
        self.assertEqual(second.status_code, 409)

    def test_managed_creation_url_urlencodes_only_public_name(self):
        route = f"/api/v1/tenants/{TENANT_A}/managed-bot-requests"
        result = self.client.post(route, json={
            "suggested_name": "My Store & Shop", "suggested_username": "MyStoreBot"
        }, headers=self.headers())
        self.assertEqual(result.status_code, 201, result.text)
        url = result.json()["creation_url"]
        self.assertEqual(url, "https://t.me/newbot/DirectPilotManagerBot/MyStoreBot?name=My%20Store%20%26%20Shop")
        self.assertNotIn("token", url.lower())

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
