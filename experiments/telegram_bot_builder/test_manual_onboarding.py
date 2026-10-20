"""Offline validation for Bring-Your-Own-Bot token onboarding."""
import unittest
import httpx
from cryptography.fernet import Fernet
from experiments.telegram_bot_builder.manual_onboarding import validate_botfather_token, BotTokenValidationError
from experiments.telegram_bot_builder.vault import TokenVault

SYNTHETIC = "123456789:" + "x" * 35

class TokenValidationTests(unittest.IsolatedAsyncioTestCase):
    async def test_valid_getme_only(self):
        def respond(request):
            self.assertTrue(str(request.url).endswith("/getMe"))
            self.assertEqual(request.method, "GET")
            return httpx.Response(200, json={"ok": True, "result": {
                "id": 321, "username": "CustomerTestBot", "first_name": "Test", "is_bot": True}})
        bot = await validate_botfather_token(SYNTHETIC, transport=httpx.MockTransport(respond))
        self.assertEqual(bot["telegram_bot_id"], 321)
        self.assertEqual(bot["username"], "CustomerTestBot")
        self.assertNotIn(SYNTHETIC, str(bot))

    async def test_rejects_non_bot(self):
        transport=httpx.MockTransport(lambda _: httpx.Response(200,json={"ok":True,"result":{"id":12,"is_bot":False,"username":"Human"}}))
        with self.assertRaises(BotTokenValidationError) as ctx:
            await validate_botfather_token(SYNTHETIC,transport=transport)
        self.assertEqual(ctx.exception.code,"telegram_invalid_identity")

    async def test_rejects_bad_token_without_call(self):
        with self.assertRaises(BotTokenValidationError) as ctx:
            await validate_botfather_token("not-a-token")
        self.assertEqual(ctx.exception.code,"invalid_token_format")

    async def test_telegram_unauthorized(self):
        transport=httpx.MockTransport(lambda _: httpx.Response(401,json={"ok":False,"description":"Secret"}))
        with self.assertRaises(BotTokenValidationError) as ctx:
            await validate_botfather_token(SYNTHETIC,transport=transport)
        self.assertEqual(ctx.exception.code,"token_rejected")

    async def test_transport_does_not_leak(self):
        def bad(request): raise httpx.ConnectError(str(request.url),request=request)
        with self.assertRaises(BotTokenValidationError) as ctx:
            await validate_botfather_token(SYNTHETIC,transport=httpx.MockTransport(bad))
        self.assertEqual(ctx.exception.code,"telegram_unavailable")
        self.assertNotIn(SYNTHETIC,str(ctx.exception))

    async def test_encrypted_bot_credential_roundtrip(self):
        vault=TokenVault(Fernet.generate_key().decode())
        sealed=vault.encrypt(SYNTHETIC)
        self.assertNotIn(SYNTHETIC.encode(),sealed)
        self.assertEqual(vault.decrypt(sealed),SYNTHETIC)

if __name__=="__main__":
    unittest.main()
