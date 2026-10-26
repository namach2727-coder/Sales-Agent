"""Offline mock-only managed credential tests. Never use live Telegram secrets."""
import asyncio
import json
import unittest
import httpx

from experiments.telegram_bot_builder.managed_credentials import (
    fetch_managed_bot_token, ManagedCredentialError,
)

MANAGER = "987654:ABCDEFGHIJKLMNOPQRSTUVWXYZabc123456"


class ManagedCredentialTests(unittest.TestCase):
    def test_success_returns_matching_child_only(self):
        def handle(request):
            self.assertEqual(request.method, "POST")
            self.assertTrue(request.url.path.endswith("/getManagedBotToken"))
            self.assertEqual(json.loads(request.content), {"user_id": 123456})
            return httpx.Response(200, json={"ok": True, "result": "123456:ABCDEFGHIJKLMNOPQRSTUVWXYZabc123456"})
        result = asyncio.run(fetch_managed_bot_token(
            MANAGER, 123456, transport=httpx.MockTransport(handle),
        ))
        self.assertTrue(result.startswith("123456:"))

    def test_wrong_identity_fails_closed(self):
        def handle(request):
            return httpx.Response(200, json={"ok": True, "result": "222222:ABCDEFGHIJKLMNOPQRSTUVWXYZabc123456"})
        with self.assertRaisesRegex(ManagedCredentialError, "managed_token_identity_mismatch"):
            asyncio.run(fetch_managed_bot_token(MANAGER, 123456, transport=httpx.MockTransport(handle)))

    def test_api_error_never_reveals_token(self):
        def handle(request):
            return httpx.Response(403, json={"ok": False, "description": "secret test"})
        with self.assertRaises(ManagedCredentialError) as ctx:
            asyncio.run(fetch_managed_bot_token(MANAGER, 123456, transport=httpx.MockTransport(handle)))
        self.assertEqual(str(ctx.exception), "manager_api_unavailable")
        self.assertNotIn(MANAGER, str(ctx.exception))
        self.assertNotIn("secret", str(ctx.exception))

    def test_validation_blocks_network(self):
        async def attempt():
            return await fetch_managed_bot_token(MANAGER, True)
        with self.assertRaisesRegex(ManagedCredentialError, "invalid_child_identity"):
            asyncio.run(attempt())


if __name__ == "__main__":
    unittest.main()
