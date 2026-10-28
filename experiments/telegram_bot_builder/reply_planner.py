"""Pure reply planning; callers load only the authorized published configuration."""
from typing import Any, Mapping
from .core import BotConfiguration, resolve_text_reply


def plan_private_reply(config: BotConfiguration, update: Mapping[str, Any], *, tenant_id: str, bot_id: int) -> dict[str, Any] | None:
    if config.tenant_id != tenant_id or config.bot_id != bot_id:
        raise ValueError('Configuration does not belong to this tenant and bot')
    message = update.get('message')
    if not isinstance(message, dict):
        return None
    sender, chat = message.get('from'), message.get('chat')
    if not isinstance(sender, dict) or sender.get('is_bot') is not False:
        return None
    if not isinstance(chat, dict) or chat.get('type') != 'private':
        return None
    chat_id, sender_id = chat.get('id'), sender.get('id')
    if type(chat_id) is not int or chat_id <= 0 or type(sender_id) is not int or sender_id != chat_id:
        return None
    text = message.get('text')
    if not isinstance(text, str) or not text.strip() or len(text) > 4096:
        return None
    return {'chat_id': chat_id, 'text': resolve_text_reply(config, text)}
