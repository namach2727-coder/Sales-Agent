"""Offline cryptographic test fixtures; synthetic IDs and secrets only."""
import base64
import hashlib
import hmac
import json
import time
import unittest
from urllib.parse import urlencode

from experiments.telegram_bot_builder.auth import TelegramAuthError, verify_init_data, safe_initdata_shape, diagnose_ed25519, diagnose_hmac_mismatch


def signed_initdata(token="111:TESTTOKEN", *, user_id=123456, now=None,
                    tamper=False, stale=0, duplicate=False, signature=False):
    now = int(time.time()) if now is None else now
    fields = {"auth_date": str(now - stale), "user": json.dumps({"id": user_id}, separators=(",", ":"))}
    if signature:
        fields["signature"] = "third-party-field"
    check = "\n".join(f"{k}={v}" for k, v in sorted(fields.items()))
    key = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    fields["hash"] = hmac.new(key, check.encode(), hashlib.sha256).hexdigest()
    if tamper:
        fields["user"] = json.dumps({"id": user_id + 5})
    raw = urlencode(fields)
    return raw + ("&user=%7B%7D" if duplicate else "")


class AuthTests(unittest.TestCase):
    def test_safe_envelope_shape_never_exposes_values(self):
        raw = signed_initdata(token="111:TESTTOKEN", now=10000, signature=True)
        result = safe_initdata_shape(raw)
        self.assertEqual(result, "q0_c0_s1_u1_a1")
        self.assertNotIn("TESTTOKEN", result)
        self.assertNotIn("123456", result)
        self.assertEqual(safe_initdata_shape(""), "absent_or_oversize")
        self.assertEqual(safe_initdata_shape("user=a&user=b"), "duplicate_fields")

    def test_ed25519_diagnostic_with_synthetic_key(self):
        from unittest.mock import patch
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        from cryptography.hazmat.primitives import serialization
        private_key = Ed25519PrivateKey.from_private_bytes(bytes(range(32)))
        public_key = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        fields = {"auth_date": "10000", "user": '{"id":123456}', "query_id": "test"}
        message = "111:WebAppData" + chr(10) + chr(10).join(
            f"{k}={v}" for k, v in sorted(fields.items())
        )
        fields["signature"] = base64.urlsafe_b64encode(
            private_key.sign(message.encode("utf-8"))
        ).decode().rstrip("=")
        raw = urlencode(fields)
        with patch("experiments.telegram_bot_builder.auth._TELEGRAM_ED25519_PROD", public_key):
            self.assertEqual(diagnose_ed25519(raw, "111:TESTTOKEN"), "valid")
            self.assertEqual(diagnose_ed25519(raw, "222:OTHER"), "invalid")
            self.assertEqual(diagnose_ed25519("", "111:TESTTOKEN"), "unavailable")

    def test_hmac_mismatch_diagnostics_are_non_authorizing(self):
        raw = signed_initdata(token="111:TESTTOKEN", now=10000, signature=True)
        self.assertEqual(diagnose_hmac_mismatch(raw, "999:WRONG"), "key_or_payload_mismatch")
        self.assertEqual(diagnose_hmac_mismatch(raw, "999:WRONG "), "token_whitespace")
        self.assertEqual(diagnose_hmac_mismatch("", "111:TESTTOKEN"), "unavailable")
        fields = {"auth_date": "10000", "user": '{"id":123456}', "signature": "synthetic"}
        check = chr(10).join(f"{k}={v}" for k, v in sorted(fields.items()))
        secret = hmac.new(b"WebAppData", b"111:TESTTOKEN", hashlib.sha256).digest()
        fields["hash"] = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
        self.assertEqual(diagnose_hmac_mismatch(urlencode(fields), "111:TESTTOKEN"), "signature_field_included")
        self.assertEqual(verify_init_data(urlencode(fields), "111:TESTTOKEN", now=10000).user_id, 123456)

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

    def test_signature_field_included_for_hmac(self):
        self.assertEqual(verify_init_data(signed_initdata(now=10000, signature=True),
                                          "111:TESTTOKEN", now=10000).user_id, 123456)

    def test_reject_signed_data_if_signature_field_modified(self):
        raw = signed_initdata(now=10000, signature=True)
        altered = raw.replace("third-party-field", "tampered-field")
        with self.assertRaises(TelegramAuthError) as ctx:
            verify_init_data(altered, "111:TESTTOKEN", now=10000)
        self.assertEqual(str(ctx.exception), "invalid_signature")

    def test_safe_auth_failure_categories(self):
        cases = [
            ("", "111:TESTTOKEN", "missing_init_data", 10000),
            (signed_initdata(now=10000), "WRONG", "invalid_signature", 10000),
            (signed_initdata(now=10000, stale=7200), "111:TESTTOKEN", "expired_auth_date", 10000),
            (signed_initdata(now=10000, duplicate=True), "111:TESTTOKEN", "malformed_init_data", 10000),
        ]
        for raw, token, reason, now in cases:
            with self.subTest(reason=reason):
                with self.assertRaises(TelegramAuthError) as ctx:
                    verify_init_data(raw, token, now=now)
                self.assertEqual(str(ctx.exception), reason)
                self.assertNotIn("TESTTOKEN", str(ctx.exception))

    def test_reject_boolean_user_id(self):
        with self.assertRaises(TelegramAuthError):
            verify_init_data(signed_initdata(user_id=True), "111:TESTTOKEN")


if __name__ == "__main__":
    unittest.main()
