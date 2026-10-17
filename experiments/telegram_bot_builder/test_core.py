"""No external Telegram calls; run with python -m unittest discover."""
import unittest

from experiments.telegram_bot_builder.core import (
    BotConfiguration, ReplyRule, build_managed_bot_request_keyboard,
    check_webhook_secret, parse_managed_bot_created, resolve_text_reply,
)


class ManagedBotSpikeTests(unittest.TestCase):
    def test_request_managed_bot_uses_official_keyboard_field(self):
        button = build_managed_bot_request_keyboard(42, suggested_name="Test Bot")["keyboard"][0][0]
        self.assertEqual(button["request_managed_bot"]["request_id"], 42)
        self.assertEqual(button["request_managed_bot"]["suggested_name"], "Test Bot")

    def test_request_id_rejects_out_of_range(self):
        with self.assertRaises(ValueError):
            build_managed_bot_request_keyboard(2**31)

    def test_parses_managed_bot_update_with_no_token(self):
        event = {"update_id": 17, "managed_bot": {
            "user": {"id": 20, "is_bot": False},
            "bot": {"id": 30, "is_bot": True, "username": "my_new_bot"},
        }}
        parsed = parse_managed_bot_created(event)
        self.assertEqual((parsed.owner_user_id, parsed.bot_id), (20, 30))
        self.assertNotIn("token", repr(parsed).lower())

    def test_parses_message_variant(self):
        event = {"update_id": 18, "message": {
            "from": {"id": 20}, "chat": {"type": "private"},
            "managed_bot_created": {"bot": {"id": 30, "is_bot": True}}
        }}
        self.assertEqual(parse_managed_bot_created(event).bot_id, 30)

    def test_rejects_unexpected_group_creation_message(self):
        event = {"update_id": 19, "message": {
            "from": {"id": 20}, "chat": {"type": "group"},
            "managed_bot_created": {"bot": {"id": 30, "is_bot": True}}
        }}
        self.assertIsNone(parse_managed_bot_created(event))

    def test_requires_matching_webhook_secret(self):
        self.assertTrue(check_webhook_secret("aB_123-xyz", "aB_123-xyz"))
        self.assertFalse(check_webhook_secret("aB_123-xyz", "wrong"))
        self.assertFalse(check_webhook_secret("", ""))
        self.assertFalse(check_webhook_secret("aB_123-xyz", None))

    def test_deterministic_rules_and_persian_normalization(self):
        settings = BotConfiguration("tenant-A", 101, "Welcome", "Fallback", (
            ReplyRule("قيمت", "قیمت محصول ۱۰۰ تومان است", "contains"),
        ))
        self.assertEqual(resolve_text_reply(settings, "قیمت لطفا"), "قیمت محصول ۱۰۰ تومان است")
        self.assertEqual(resolve_text_reply(settings, "/start"), "Welcome")
        self.assertEqual(resolve_text_reply(settings, "other"), "Fallback")

    def test_tenant_configs_are_independent(self):
        a = BotConfiguration("tenant-A", 101, "Hi A", "Unknown A")
        b = BotConfiguration("tenant-B", 102, "Hi B", "Unknown B")
        self.assertEqual(resolve_text_reply(a, "/start"), "Hi A")
        self.assertEqual(resolve_text_reply(b, "/start"), "Hi B")


if __name__ == "__main__":
    unittest.main()
