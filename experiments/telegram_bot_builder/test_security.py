"""Offline cryptographic test fixtures; synthetic IDs and secrets only."""
import hashlib
import hmac
import json
import time
import unittest
from urllib.parse import urlencode

from experiments.telegram_bot_builder.auth import TelegramAuthError, verify_init_data


def signed_initdata(token="111:TESTTOKEN", *, user_id=123456, now=None,
                    tamper=False, stale=0, duplicate=False, signature=False):
    now = int(time.time()) if now is None else now
    fields = {"auth_date": str(now - stale), "user": json.dumps({"id": user_id}, separators=(",", ":"))}
    check = "\n".join(f"{k}={v}" for k, v in sorted(fields.items()))
    key = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    fields["hash"] = hmac.new(key, check.encode(), hashlib.sha256).hexdigest()
    if tamper:
        fields["user"] = json.dumps({"id": user_id + 5})
    if signature:
        fields["signature"] = "third-party-field"
    raw = urlencode(fields)
    return raw + ("&user=%7B%7D" if duplicate else "")


class AuthTests(unittest.TestCase):
    def test_correct_user(self):
        raw = signed_initdata(now=10000)
        self.assertEqual(verify_init_data(raw, "111:TESTTOKEN", now=10000).user_id, 123456)

    def test_reject_tamper_wrong_token(self):
        for raw, token in [(signed_initdata(tamper=True), "111:TESTTOKEN"),
                           (signed_initdata(), "WRONG")]:
            with self.assertRaises(TelegramAuthError):
                verify_init_data(raw, token)

    def test_reject_replay_duplicates_future(self):
        for raw, now in [
            (signed_initdata(now=10000, stale=7200), 10000),
            (signed_initdata(now=10000, duplicate=True), 10000),
            (signed_initdata(now=11000), 10000),
        ]:
            with self.assertRaises(TelegramAuthError):
                verify_init_data(raw, "111:TESTTOKEN", now=now)

    def test_no_token_is_fail_closed(self):
        with self.assertRaises(TelegramAuthError):
            verify_init_data(signed_initdata(), "")

    def test_signature_field_ignored_for_hmac(self):
        self.assertEqual(verify_init_data(signed_initdata(now=10000, signature=True),
                                          "111:TESTTOKEN", now=10000).user_id, 123456)

    def test_reject_boolean_user_id(self):
        with self.assertRaises(TelegramAuthError):
            verify_init_data(signed_initdata(user_id=True), "111:TESTTOKEN")


if __name__ == "__main__":
    unittest.main()
