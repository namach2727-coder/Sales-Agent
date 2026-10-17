"""Token-free building blocks for a prospective standalone Telegram bot-builder.

SPIKE ONLY. No database, network calls, webhook registration, or production routes.
Telegram API docs: https://core.telegram.org/bots/api
"""

from __future__ import annotations

from dataclasses import dataclass
import hmac
import re
import unicodedata
from typing import Any, Mapping, Literal


_ALLOWED_SECRET = re.compile(r"^[A-Za-z0-9_-]{1,256}$")
MatchMode = Literal["exact", "contains"]


@dataclass(frozen=True, slots=True)
class ReplyRule:
    keyword: str
    reply: str
    match_mode: MatchMode = "exact"

    def __post_init__(self) -> None:
        if not self.keyword.strip() or len(self.keyword) > 120:
            raise ValueError("keyword must contain 1 to 120 characters")
        if not self.reply.strip() or len(self.reply) > 4096:
            raise ValueError("reply must contain 1 to 4096 characters")
        if self.match_mode not in ("exact", "contains"):
            raise ValueError("unsupported matching mode")


@dataclass(frozen=True, slots=True)
class BotConfiguration:
    """Opaque tenant-owned configuration. Router MUST scope by bot and tenant."""

    tenant_id: str
    bot_id: int
    start_message: str
    fallback_message: str
    rules: tuple[ReplyRule, ...] = ()

    def __post_init__(self) -> None:
        if not self.tenant_id.strip() or self.bot_id <= 0:
            raise ValueError("bot must be bound to a tenant and positive bot ID")
        if not self.start_message.strip() or not self.fallback_message.strip():
            raise ValueError("start and fallback messages are required")
        if any(len(msg) > 4096 for msg in (self.start_message, self.fallback_message)):
            raise ValueError("message exceeds Telegram text limit")


@dataclass(frozen=True, slots=True)
class ManagedBotCreated:
    update_id: int
    owner_user_id: int
    bot_id: int
    bot_username: str | None


def build_managed_bot_request_keyboard(
    request_id: int, *, suggested_name: str = "My Bot", suggested_username: str | None = None
) -> dict[str, Any]:
    """Prompt customer to create a Managed Bot via the official Telegram client.

    Requires the manager bot to have bot-management enabled in @BotFather Mini App.
    Telegram clients require user confirmation; this DOES NOT create a bot itself.
    """
    if not isinstance(request_id, int) or isinstance(request_id, bool) or not (-2**31 <= request_id < 2**31):
        raise ValueError("request_id must be a signed 32-bit integer")
    if not 1 <= len(suggested_name.strip()) <= 64:
        raise ValueError("suggested_name must contain 1 to 64 characters")
    request: dict[str, Any] = {
        "request_id": request_id,
        "suggested_name": suggested_name.strip(),
    }
    if suggested_username is not None:
        username = suggested_username.lstrip("@")
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{3,30}bot", username, flags=re.IGNORECASE):
            raise ValueError("suggested_username must be a plausible Telegram bot username")
        request["suggested_username"] = username
    return {
        "keyboard": [[{"text": "Create my Telegram bot", "request_managed_bot": request}]],
        "resize_keyboard": True,
        "one_time_keyboard": True,
    }


def parse_managed_bot_created(update: Mapping[str, Any]) -> ManagedBotCreated | None:
    """Parse one verified manager-bot update, without fetching or exposing bot tokens.

    Supports Telegram's managed_bot update and message.managed_bot_created form.
    Caller must authenticate the webhook, deduplicate update_id, and authorize owner.
    """
    update_id = update.get("update_id")
    if not isinstance(update_id, int) or isinstance(update_id, bool) or update_id < 0:
        return None
    event = update.get("managed_bot")
    if isinstance(event, dict):
        owner = event.get("user")
        bot = event.get("bot")
    else:
        message = update.get("message")
        if not isinstance(message, dict):
            return None
        creation = message.get("managed_bot_created")
        if not isinstance(creation, dict):
            return None
        owner = message.get("from")
        bot = creation.get("bot")
        chat = message.get("chat")
        if not isinstance(chat, dict) or chat.get("type") != "private":
            return None
    if not isinstance(owner, dict) or not isinstance(bot, dict):
        return None
    owner_id, bot_id = owner.get("id"), bot.get("id")
    if (
        not isinstance(owner_id, int) or isinstance(owner_id, bool) or owner_id <= 0
        or not isinstance(bot_id, int) or isinstance(bot_id, bool) or bot_id <= 0
        or bot.get("is_bot") is not True
    ):
        return None
    username = bot.get("username")
    return ManagedBotCreated(
        update_id=update_id,
        owner_user_id=owner_id,
        bot_id=bot_id,
        bot_username=username if isinstance(username, str) else None,
    )


def check_webhook_secret(expected: str, received: str | None) -> bool:
    """Validate X-Telegram-Bot-Api-Secret-Token, failing closed."""
    if not expected or not _ALLOWED_SECRET.fullmatch(expected):
        return False
    if not received or not _ALLOWED_SECRET.fullmatch(received):
        return False
    return hmac.compare_digest(expected, received)


def _normalize(message: str) -> str:
    # Persian ya/kaf normalization plus casefold for bilingual rule matching.
    return unicodedata.normalize("NFKC", message).translate(
        str.maketrans({"ي": "ی", "ك": "ک"})
    ).casefold().strip()


def resolve_text_reply(config: BotConfiguration, text: str) -> str:
    """Deterministic text rules for a single authorized tenant/bot configuration."""
    normalized = _normalize(text)
    if normalized.split("@", 1)[0] == "/start":
        return config.start_message
    for rule in config.rules:
        keyword = _normalize(rule.keyword)
        if normalized == keyword or (rule.match_mode == "contains" and keyword in normalized):
            return rule.reply
    return config.fallback_message
