"""Authenticated draft selection with synthetic data and effects forbidden."""
import os
import unittest
from contextlib import ExitStack
from unittest.mock import patch

from fastapi.testclient import TestClient

from experiments.telegram_bot_builder.api import app, get_connection
from experiments.telegram_bot_builder.test_api import (
    BOT_A, BOT_B, TENANT_A, TENANT_B, Cursor, FakeDB,
)
from experiments.telegram_bot_builder.test_security import signed_initdata


class PreviewDB(FakeDB):
    def execute(self, query, args=()):
        sql = ' '.join(query.split())
        # Only the tenant role and bot identity may be read, never saved rules/keys.
        if not (sql.startswith('SELECT tu.role') or sql.startswith('SELECT id,telegram_bot_id')):
            raise AssertionError('Preview attempted an unexpected database operation')
        if 'FROM telbot.tenant_users tu' in sql and args == (TENANT_A, 333444):
            self.commands.append((sql, tuple(args)))
            return Cursor({'role': 'editor'})
        return super().execute(query, args)

    def commit(self):
        raise AssertionError('Preview must not commit')


class ResponsePreviewTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.db = PreviewDB()
        app.dependency_overrides[get_connection] = lambda: self.db
        self.stack.enter_context(patch.dict(os.environ, {
            'TELBOT_MANAGER_TOKEN': '111:TESTTOKEN', 'TELBOT_ENV': 'uat',
            'TELBOT_REPLIES_ENABLED': 'true', 'TELBOT_EXTERNAL_API_ENABLED': 'true',
        }))
        self.effects = [self.stack.enter_context(patch(target, side_effect=AssertionError('Unexpected effect')))
                        for target in (
                            'experiments.telegram_bot_builder.api_actions.invoke_api',
                            'experiments.telegram_bot_builder.api_actions.open_call',
                            'experiments.telegram_bot_builder.reply_runtime.invoke_api',
                            'experiments.telegram_bot_builder.reply_runtime.send_text',
                            'experiments.telegram_bot_builder.vault.TokenVault.decrypt',
                        )]
        self.client = TestClient(app)
        self.base = f'/api/v1/tenants/{TENANT_A}/bots/{BOT_A}/preview'
        self.headers = {'X-Telegram-Init-Data': signed_initdata()}

    def tearDown(self):
        try:
            for effect in self.effects:
                effect.assert_not_called()
            self.assertEqual(self.db.commits, 0)
        finally:
            app.dependency_overrides.clear()
            self.client.close()
            self.stack.close()

    def preview(self, text, rules=None, **extra):
        return self.client.post(self.base, headers=self.headers, json={
            'greeting': 'Unsaved hello', 'fallback_reply': 'Unsaved fallback',
            'rules': [] if rules is None else rules, 'text': text, **extra,
        })

    def test_start_uses_unsaved_greeting_before_any_rule(self):
        for text in ['/start', ' /START@ExampleBot payload ']:
            response = self.preview(text, [{'keyword': '/start', 'match_mode': 'contains', 'response_text': 'Other'}])
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(response.json(), {'action': 'greeting', 'response_text': 'Unsaved hello', 'executed': False})
        self.assertEqual(len(self.db.commands), 4)

    def test_disabled_rules_order_exact_contains_and_persian_normalization(self):
        rules = [
            {'keyword': 'قیمت', 'response_text': 'Disabled', 'enabled': False},
            {'keyword': 'علي', 'response_text': 'Normalized'},
            {'keyword': 'قیمت', 'response_text': 'First', 'match_mode': 'contains'},
            {'keyword': 'قیمت', 'response_text': 'Second'},
        ]
        for text, action, answer, index in [
            ('قیمت', 'text', 'First', 3), ('قیمت محصول', 'text', 'First', 3),
            ('علی', 'text', 'Normalized', 2), ('علی دیگر', 'fallback', 'Unsaved fallback', None),
            ('unknown', 'fallback', 'Unsaved fallback', None),
        ]:
            with self.subTest(text=text):
                result = self.preview(text, rules).json()
                self.assertEqual((result['action'], result['response_text'], result.get('rule_index')), (action, answer, index))
                self.assertIs(result['executed'], False)

    def test_api_preview_only_identifies_rule_and_fallback_even_when_flags_on(self):
        response = self.preview('stock', [{
            'keyword': 'stock', 'response_text': 'Provider unavailable', 'action_type': 'api',
            'api': {'url': 'https://api.example.com/stock', 'method': 'POST',
                    'auth_mode': 'bearer', 'credential': 'synthetic-preview-secret',
                    'json_body': {'query': 'sample'}, 'response_path': 'data.answer'},
        }])
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json(), {'action': 'api', 'rule_index': 1, 'fallback_text': 'Provider unavailable', 'executed': False})
        self.assertNotIn('synthetic-preview-secret', response.text)
        self.assertNotIn('api.example.com', response.text)

    def test_editor_allowed_viewer_other_tenant_and_other_bot_denied(self):
        self.headers = {'X-Telegram-Init-Data': signed_initdata(user_id=333444)}
        self.assertEqual(self.preview('hello').status_code, 200)
        for user, tenant, bot, status in [
            (111222, TENANT_A, BOT_A, 403), (123456, TENANT_B, BOT_A, 403),
            (123456, TENANT_A, BOT_B, 404),
        ]:
            self.headers = {'X-Telegram-Init-Data': signed_initdata(user_id=user)}
            self.base = f'/api/v1/tenants/{tenant}/bots/{bot}/preview'
            self.assertEqual(self.preview('hello').status_code, status)

    def test_authentication_required(self):
        self.headers = {}
        self.assertEqual(self.preview('hello').status_code, 401)
        self.assertEqual(self.db.commands, [])

    def test_validation_hides_entire_body_and_requires_bounded_explicit_snapshot(self):
        for text, rules in [
            ('', []), ('  ', []), ('a' * 4097, []), ('a', None),
            ('a', [{'keyword': 'a', 'response_text': 'b'}] * 101),
            ('a', [{'keyword': 'a', 'response_text': 'b', 'action_type': 'api',
                    'api': {'url': 'http://bad.example.com', 'credential': 'synthetic-preview-secret'}}]),
        ]:
            response = self.client.post(self.base, headers=self.headers, json={
                'text': text, 'rules': rules, 'greeting': 'Hello', 'fallback_reply': 'Fallback',
            })
            self.assertEqual(response.status_code, 422, response.text)
            self.assertEqual(response.json(), {'detail': 'Invalid bot configuration'})
        response = self.client.post(self.base, headers=self.headers, json={
            'text': 'hello', 'greeting': 'Hello', 'fallback_reply': 'Fallback',
        })
        self.assertEqual(response.status_code, 422)
