"""Offline-only Telegram transport payload validation for DirectPilot TelBot.

This module deliberately does not send requests or access credentials.
Only a separately approved UAT transport may invoke Telegram Bot API.
"""
from __future__ import annotations

import json
from typing import Any, Mapping


def build_manager_keyboard_message(
    chat_id: int, reply_markup: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate the managed-bot button prepared by the authorized ticket API.

    A ticket's reply_markup is *not_sent*. This function only prepares the
    eventual sendMessage body, never changes that delivery status.
    """
    if type(chat_id) is not int or chat_id <= 0:
        raise ValueError("chat_id must be a positive Telegram user ID")
    if not isinstance(reply_markup, Mapping):
        raise ValueError("reply_markup is required")
    keyboard = reply_markup.get("keyboard")
    if not isinstance(keyboard, list) or len(keyboard) != 1:
        raise ValueError("exactly one keyboard row is required")
    row = keyboard[0]
    if not isinstance(row, list) or len(row) != 1:
        raise ValueError("exactly one managed-bot button is required")
    button = row[0]
    if not isinstance(button, dict) or not isinstance(button.get("text"), str):
        raise ValueError("invalid keyboard button")
    request = button.get("request_managed_bot")
    if not isinstance(request, dict):
        raise ValueError("managed bot request is missing")
    request_id = request.get("request_id")
    if type(request_id) is not int or not 0 < request_id < 2**31:
        raise ValueError("invalid managed bot request ID")
    if not isinstance(request.get("suggested_name"), str) or not request["suggested_name"].strip():
        raise ValueError("invalid bot name")
    # Prevent arbitrary reply markup or additional outbound actions being
    # smuggled through a user-facing delivery endpoint.
    if set(button) != {"text", "request_managed_bot"}:
        raise ValueError("unexpected keyboard button fields")
    if set(request) - {"request_id", "suggested_name", "suggested_username"}:
        raise ValueError("unexpected managed-bot request fields")
    if set(reply_markup) - {"keyboard", "resize_keyboard", "one_time_keyboard"}:
        raise ValueError("unexpected keyboard fields")
    if len(json.dumps(reply_markup, ensure_ascii=False).encode("utf-8")) > 4096:
        raise ValueError("keyboard exceeds safety limit")
    return {
        "chat_id": chat_id,
        "text": "برای ساخت ربات خود، دکمه زیر را انتخاب و درخواست تلگرام را تأیید کنید.",
        "reply_markup": dict(reply_markup),
        "protect_content": True,
    }
