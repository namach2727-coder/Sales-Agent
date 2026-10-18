"""Pure offline tests: no Telegram credentials, network or database access."""
import unittest

from experiments.telegram_bot_builder.core import build_managed_bot_request_keyboard
from experiments.telegram_bot_builder.delivery_contract import build_manager_keyboard_message


class ManagerDeliveryContractTests(unittest.TestCase):
    def setUp(self):
        self.markup = build_managed_bot_request_keyboard(42, suggested_name="My Store")

    def test_builds_offline_message_for_same_owner(self):
        result = build_manager_keyboard_message(123456, self.markup)
        self.assertEqual(result["chat_id"], 123456)
        self.assertEqual(result["reply_markup"]["keyboard"][0][0]["request_managed_bot"]["request_id"], 42)
        self.assertTrue(result["protect_content"])
        self.assertNotIn("token", repr(result).lower())

    def test_rejects_invalid_chat_identity(self):
        for value in (0, -1, True, "123456", None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                build_manager_keyboard_message(value, self.markup)

    def test_rejects_arbitrary_keyboard_actions(self):
        markup = build_managed_bot_request_keyboard(42)
        markup["keyboard"][0][0]["web_app"] = {"url": "https://invalid.example"}
        with self.assertRaises(ValueError):
            build_manager_keyboard_message(123, markup)

    def test_rejects_invalid_ticket(self):
        markup = build_managed_bot_request_keyboard(42)
        markup["keyboard"][0][0]["request_managed_bot"]["request_id"] = True
        with self.assertRaises(ValueError):
            build_manager_keyboard_message(123, markup)

    def test_rejects_extra_markup(self):
        markup = build_managed_bot_request_keyboard(42)
        markup["inline_keyboard"] = []
        with self.assertRaises(ValueError):
            build_manager_keyboard_message(123, markup)


if __name__ == "__main__":
    unittest.main()
