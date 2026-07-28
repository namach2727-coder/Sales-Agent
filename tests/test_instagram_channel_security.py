from __future__ import annotations

import hashlib
import hmac

import pytest
from cryptography.fernet import Fernet

from app.config import Settings
from app.instagram_channel.exceptions import (
    InstagramCredentialConfigurationError,
    InstagramWebhookSecurityError,
)
from app.instagram_channel.security import (
    FernetTokenCipher,
    valid_fernet_key,
    verify_meta_signature,
    verify_subscription,
)


def test_token_cipher_uses_authenticated_encryption_without_plaintext() -> None:
    key = Fernet.generate_key().decode("ascii")
    cipher = FernetTokenCipher(key)
    plaintext = "secret-meta-access-token"
    ciphertext = cipher.encrypt(plaintext)
    assert plaintext not in ciphertext
    assert cipher.decrypt(ciphertext) == plaintext


@pytest.mark.parametrize("key", ["", "replace-me", "a" * 44])
def test_token_cipher_fails_closed_for_invalid_key(key: str) -> None:
    assert valid_fernet_key(key) is False
    with pytest.raises(InstagramCredentialConfigurationError):
        FernetTokenCipher(key)


def test_token_cipher_loads_secret_from_settings_without_exposing_it() -> None:
    key = Fernet.generate_key().decode("ascii")
    settings = Settings(instagram_token_encryption_key=key)
    cipher = FernetTokenCipher.from_settings(settings)
    assert cipher.decrypt(cipher.encrypt("token")) == "token"
    assert key not in repr(settings.instagram_token_encryption_key)


def test_webhook_subscription_requires_exact_constant_time_token_contract() -> None:
    assert (
        verify_subscription(
            mode="subscribe",
            challenge="challenge-exact",
            supplied_token="verify-secret",
            configured_token="verify-secret",
        )
        == "challenge-exact"
    )
    for supplied in (None, "", "wrong"):
        with pytest.raises(InstagramWebhookSecurityError):
            verify_subscription(
                mode="subscribe",
                challenge="challenge",
                supplied_token=supplied,
                configured_token="verify-secret",
            )
    with pytest.raises(InstagramWebhookSecurityError):
        verify_subscription(
            mode="unsubscribe",
            challenge="challenge",
            supplied_token="verify-secret",
            configured_token="verify-secret",
        )


def test_meta_signature_is_verified_against_exact_raw_bytes() -> None:
    secret = "meta-app-secret"
    body = b'{"entry":[],"object":"instagram"}'
    digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    verify_meta_signature(body, f"sha256={digest}", secret)
    with pytest.raises(InstagramWebhookSecurityError):
        verify_meta_signature(body + b" ", f"sha256={digest}", secret)


@pytest.mark.parametrize(
    "header",
    [None, "", "sha1=abc", "sha256=invalid", "sha256=" + ("0" * 63)],
)
def test_meta_signature_rejects_missing_or_malformed_values(
    header: str | None,
) -> None:
    with pytest.raises(InstagramWebhookSecurityError):
        verify_meta_signature(b"{}", header, "secret")


def test_meta_signature_fails_closed_without_app_secret() -> None:
    with pytest.raises(InstagramWebhookSecurityError):
        verify_meta_signature(b"{}", "sha256=" + ("0" * 64), "")
