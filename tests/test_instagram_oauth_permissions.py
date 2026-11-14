from __future__ import annotations

import pytest

from app.instagram_onboarding.provider import (
    INSTAGRAM_LOGIN_SCOPES,
    InstagramOAuthError,
    _log_short_token_permissions,
    _normalize_short_token_payload,
)


def test_normalize_flat_instagram_login_token_response() -> None:
    payload = {"access_token": "secret", "user_id": "1784", "permissions": ",".join(INSTAGRAM_LOGIN_SCOPES)}
    assert _normalize_short_token_payload(payload) == payload


def test_normalize_meta_documented_single_item_data_envelope() -> None:
    payload = {
        "data": [
            {
                "access_token": "secret",
                "user_id": "1784",
                "permissions": ",".join(INSTAGRAM_LOGIN_SCOPES),
            }
        ]
    }
    normalized = _normalize_short_token_payload(payload)
    assert normalized["user_id"] == "1784"
    assert normalized["permissions"] == ",".join(INSTAGRAM_LOGIN_SCOPES)


@pytest.mark.parametrize(
    "payload",
    [
        None,
        [],
        {"data": []},
        {"data": [{"access_token": "one"}, {"access_token": "two"}]},
        {"access_token": "top-level", "data": [{"access_token": "nested"}]},
        {"data": ["not-an-object"]},
    ],
)
def test_reject_invalid_or_ambiguous_token_response_shapes(payload: object) -> None:
    with pytest.raises(InstagramOAuthError) as raised:
        _normalize_short_token_payload(payload)
    assert raised.value.code == "oauth_token_exchange_failed"


def test_permission_parser_returns_only_granted_permission_names() -> None:
    granted = _log_short_token_permissions(
        {"permissions": "instagram_business_basic, instagram_business_manage_messages"}
    )
    assert granted == (
        "instagram_business_basic",
        "instagram_business_manage_messages",
    )


def test_permission_parser_supports_string_list_and_ignores_invalid_values() -> None:
    granted = _log_short_token_permissions(
        {"permissions": ["instagram_business_basic", None, " ", "instagram_business_manage_comments"]}
    )
    assert granted == (
        "instagram_business_basic",
        "instagram_business_manage_comments",
    )


def test_missing_permissions_are_not_synthesized_from_requested_scopes() -> None:
    granted = _log_short_token_permissions({})
    assert granted == ()
    assert set(INSTAGRAM_LOGIN_SCOPES).difference(granted) == set(INSTAGRAM_LOGIN_SCOPES)
