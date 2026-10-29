import asyncio
import unittest
import os
from unittest.mock import patch
import httpx
from experiments.telegram_bot_builder.reply_runtime import send_text, process_reply


class TransportTests(unittest.TestCase):
    def test_successful_transport(self):
        transport = httpx.MockTransport(lambda r: httpx.Response(200, json={'ok': True, 'result': {'message_id': 7}}))
        assert asyncio.run(send_text('synthetic', {'chat_id': 1, 'text': 'hello'}, transport=transport)) == (7, None)


    def test_timeout_is_uncertain_without_secret(self):
        def timeout(request):
            raise httpx.ReadTimeout('secret-bearing upstream URL', request=request)
        assert asyncio.run(send_text('synthetic', {}, transport=httpx.MockTransport(timeout))) == (None, 'delivery_unknown')


    def test_rejected_transport(self):
        transport = httpx.MockTransport(lambda r: httpx.Response(429, json={'ok': False}))
        assert asyncio.run(send_text('synthetic', {}, transport=transport)) == (None, 'telegram_rejected')


    def test_disabled_runtime_never_touches_database(self):
        with patch.dict(os.environ, {'TELBOT_ENV': 'uat', 'TELBOT_REPLIES_ENABLED': 'false'}):
            asyncio.run(process_reply(None, None, None, None))


    def test_non_uat_runtime_never_touches_database(self):
        with patch.dict(os.environ, {'TELBOT_ENV': 'production', 'TELBOT_REPLIES_ENABLED': 'true'}):
            asyncio.run(process_reply(None, None, None, None))

class RuntimeTests(unittest.IsolatedAsyncioTestCase):
    async def test_published_reply_is_committed_before_send(self):
        from unittest.mock import AsyncMock
        from cryptography.fernet import Fernet
        from experiments.telegram_bot_builder.vault import TokenVault
        key = Fernet.generate_key().decode()
        token = '42:synthetic-only'
        class Cursor:
            def __init__(self, value): self.value = value
            def fetchone(self): return self.value
            def fetchall(self): return self.value
        class Database:
            def __init__(self): self.events = []; self.paused = False; self.published = True
            def commit(self): self.events.append('commit')
            def execute(self, sql, args):
                self.events.append((sql, args))
                if 'FROM telbot.configuration_versions' in sql:
                    return Cursor({'id': 'config', 'greeting': 'Hello', 'fallback_reply': 'Fallback'} if self.published else None)
                if 'FROM telbot.reply_rules' in sql: return Cursor([])
                if 'INSERT INTO telbot.chat_sessions' in sql: return Cursor({'id': 'session', 'status': 'paused' if self.paused else 'open'})
                if 'INSERT INTO telbot.outbound_messages' in sql: return Cursor({'id': 'outbound'})
                return Cursor(None)
        db = Database()
        bot = {'id': 'bot', 'tenant_id': 'tenant', 'credential_ciphertext': TokenVault(key).encrypt(token)}
        event = {'_bot_id': 42, 'message': {'text': '/start', 'from': {'id': 123, 'is_bot': False}, 'chat': {'id': 123, 'type': 'private'}}}
        async def sent(credential, payload):
            self.assertEqual(db.events[-1], 'commit')
            self.assertEqual(credential, token)
            self.assertEqual(payload, {'chat_id': 123, 'text': 'Hello', 'reply_markup': {'remove_keyboard': True}})
            return 7, None
        with patch.dict(os.environ, {'TELBOT_ENV': 'uat', 'TELBOT_REPLIES_ENABLED': 'true', 'TELBOT_TOKEN_FERNET_KEY': key}):
            with patch('experiments.telegram_bot_builder.reply_runtime.send_text', side_effect=sent) as sender:
                await process_reply(db, bot, event, 'inbound')
                self.assertEqual(sender.call_count, 1)
                self.assertTrue(any(isinstance(e, tuple) and 'UPDATE telbot.outbound_messages' in e[0] and e[1][0] == 'sent' for e in db.events))
            for mode in ['paused', 'unpublished', 'wrong_token']:
                db = Database(); db.paused = mode == 'paused'; db.published = mode != 'unpublished'
                chosen_bot = dict(bot)
                if mode == 'wrong_token': chosen_bot['credential_ciphertext'] = TokenVault(key).encrypt('43:synthetic-only')
                with patch('experiments.telegram_bot_builder.reply_runtime.send_text', new_callable=AsyncMock) as sender:
                    await process_reply(db, chosen_bot, event, 'inbound')
                    sender.assert_not_called()
            db = Database()
            with patch('experiments.telegram_bot_builder.reply_runtime.send_text', new_callable=AsyncMock, return_value=(None, 'delivery_unknown')) as sender:
                await process_reply(db, bot, event, 'inbound')
                self.assertEqual(sender.call_count, 1)
                self.assertTrue(any(isinstance(e, tuple) and 'UPDATE telbot.outbound_messages' in e[0] and e[1][0] == 'failed' and e[1][2] == 'delivery_unknown' for e in db.events))
