"""Offline manual BotFather token validation; no real Telegram traffic."""
import unittest
import httpx
from fastapi import HTTPException
from experiments.telegram_bot_builder.manual_connect import validate_botfather_token

TOKEN = "12345678:" + "a" * 35

class ManualConnectTests(unittest.IsolatedAsyncioTestCase):
    async def test_valid_bot(self):
        def handler(req):
            self.assertEqual(req.method, "GET")
            self.assertTrue(str(req.url).endswith("/getMe"))
            return httpx.Response(200,json={"ok":True,"result":{"id":12345,"is_bot":True,"username":"Example_bot","first_name":"Example"}})
        identity=await validate_botfather_token(TOKEN,httpx.MockTransport(handler))
        self.assertEqual(identity,{"telegram_bot_id":12345,"username":"Example_bot","display_name":"Example"})
        self.assertNotIn(TOKEN,str(identity))

    async def test_invalid_token_prevents_http(self):
        with self.assertRaises(HTTPException) as error:
            await validate_botfather_token("invalid")
        self.assertEqual(error.exception.status_code,422)

    async def test_telegram_rejects_token(self):
        t=httpx.MockTransport(lambda req:httpx.Response(401,json={"ok":False,"description":"secret"}))
        with self.assertRaises(HTTPException) as error:
            await validate_botfather_token(TOKEN,t)
        self.assertEqual(error.exception.status_code,422)
        self.assertNotIn("secret",str(error.exception.detail))

    async def test_wrong_identity(self):
        t=httpx.MockTransport(lambda req:httpx.Response(200,json={"ok":True,"result":{"is_bot":False,"username":"user"}}))
        with self.assertRaises(HTTPException) as error:
            await validate_botfather_token(TOKEN,t)
        self.assertEqual(error.exception.status_code,422)

    async def test_network_failure_never_leaks_url(self):
        def fail(req):
            raise httpx.ConnectError(str(req.url),request=req)
        with self.assertRaises(HTTPException) as error:
            await validate_botfather_token(TOKEN,httpx.MockTransport(fail))
        self.assertEqual(error.exception.status_code,503)
        self.assertNotIn(TOKEN,str(error.exception.detail))

if __name__=="__main__":
    unittest.main()
