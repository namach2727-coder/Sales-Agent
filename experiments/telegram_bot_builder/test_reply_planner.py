import unittest
from experiments.telegram_bot_builder.core import BotConfiguration, ReplyRule
from experiments.telegram_bot_builder.reply_planner import plan_private_reply


def configuration():
    return BotConfiguration('tenant-a', 42, 'Welcome', 'Fallback', (ReplyRule('قیمت', 'Price'),))


def update(text='/start'):
    return {'update_id': 1, 'message': {'from': {'id': 123, 'is_bot': False}, 'chat': {'id': 123, 'type': 'private'}, 'text': text}}


class PlannerTests(unittest.TestCase):
    def test_reply_selection(self):
        for text, expected in [('/start', 'Welcome'), ('/start campaign', 'Welcome'), ('قیمت', 'Price'), ('unknown', 'Fallback')]:
            with self.subTest(text=text):
                self.assertEqual(plan_private_reply(configuration(), update(text), tenant_id='tenant-a', bot_id=42), {'chat_id': 123, 'text': expected})

    def test_cross_scope_rejected(self):
        for tenant, bot in [('tenant-b', 42), ('tenant-a', 43)]:
            with self.assertRaises(ValueError):
                plan_private_reply(configuration(), update(), tenant_id=tenant, bot_id=bot)

    def test_ignored_messages(self):
        for case in ['bot', 'group', 'foreign_sender', 'no_text', 'edited']:
            event = update()
            if case == 'bot': event['message']['from']['is_bot'] = True
            if case == 'group': event['message']['chat']['type'] = 'group'
            if case == 'foreign_sender': event['message']['from']['id'] = 456
            if case == 'no_text': event['message'].pop('text')
            if case == 'edited': event['edited_message'] = event.pop('message')
            with self.subTest(case=case):
                self.assertIsNone(plan_private_reply(configuration(), event, tenant_id='tenant-a', bot_id=42))
