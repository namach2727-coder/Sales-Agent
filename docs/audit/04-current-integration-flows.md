# AUDIT-01 — Current Integration Flows

All four integrations call `app/chat.py::process_chat()`, which is deterministic; no LLM or AI provider call occurs.

## A. Instagram inbound message

```mermaid
sequenceDiagram
    participant Meta
    participant Hook as receive_instagram_webhook
    participant DB
    participant Chat as process_chat
    participant Graph as Instagram Graph API
    Meta->>Hook: POST /webhooks/instagram
    Hook->>Hook: verify_meta_signature + JSON + extract_incoming_messages
    Hook->>DB: dedupe/persist InstagramEvent
    Hook->>DB: store_for_instagram_account + module_enabled
    Hook->>Chat: text, sender, channel, store slug
    Chat->>DB: Customer / Conversation / optional Order
    Chat-->>Hook: deterministic reply
    Hook->>Graph: synchronous POST account/messages when sending enabled
    Hook->>DB: sent/simulated/failed status
    Hook-->>Meta: processing summary
```

Evidence: `app/instagram.py::receive_instagram_webhook()`, `extract_incoming_messages()`, `deliver_response()`, `InstagramClient.send_text()`; persistence models are `InstagramEvent`, `Customer`, `Conversation`, and optional `Order`. Echo/self/deleted/non-text/empty messages are skipped. The outbound `httpx` call is awaited inside webhook processing.

## B. Instagram comment

```mermaid
sequenceDiagram
    participant Meta
    participant Hook as receive_instagram_webhook
    participant DB
    participant Graph as Instagram Graph API
    Meta->>Hook: POST comment webhook
    Hook->>Hook: signature + extract_incoming_comments
    Hook->>DB: dedupe/persist InstagramCommentEvent
    Hook->>DB: store/module/price phrase/media-product lookup
    alt mapped price comment
        Hook->>Graph: synchronous private reply POST
        Hook->>DB: reply status/IDs
        Hook->>Graph: synchronous public comment reply POST
        Hook->>DB: InstagramCommentPublicReply
    else unsupported/unmapped
        Hook->>DB: ignored/unmapped status
    end
    Hook-->>Meta: processing summary
```

Evidence: `app/instagram.py::extract_incoming_comments()`, `is_price_comment()`, `deliver_comment_response()`, `ensure_public_comment_reply()`, and `InstagramClient.send_private_reply()/send_public_comment_reply()`. Product selection uses `InstagramMediaProduct`; comments do not call `process_chat()`.

## C. Telegram inbound message

```mermaid
sequenceDiagram
    participant Telegram
    participant Hook as receive_telegram_webhook/process_telegram_payload
    participant DB
    participant Chat as process_chat
    participant BotAPI as Telegram Bot API
    Telegram->>Hook: POST /webhooks/telegram + secret header
    Hook->>Hook: verify secret + extract private text
    Hook->>DB: dedupe/persist TelegramEvent
    Hook->>Chat: normalized text and telegram-prefixed identity
    Chat->>DB: Customer / Conversation / optional Order
    Chat-->>Hook: deterministic reply
    Hook->>BotAPI: synchronous sendMessage when enabled
    Hook->>DB: sent/simulated/failed status
    Hook-->>Telegram: JSON summary (503 when failures exist)
```

Evidence: `app/telegram.py::receive_telegram_webhook()`, `extract_incoming_messages()`, `process_telegram_payload()`, `deliver_response()`, and `TelegramClient.send_text()`. Alternative local polling is `app/telegram_polling.py::run_polling()`, which synchronously long-polls `getUpdates` before passing each update to the same processor. Groups, channels, bots, edited messages, and media are ignored.

## D. ManyChat inbound message

```mermaid
sequenceDiagram
    participant ManyChat
    participant Adapter as receive_manychat_instagram
    participant DB
    participant Chat as process_chat
    ManyChat->>Adapter: POST Dynamic Block + bearer
    Adapter->>Adapter: Pydantic validation + request hash
    Adapter->>DB: dedupe/persist ManyChatEvent
    Adapter->>Chat: last_input_text and ManyChat-prefixed identity
    Chat->>DB: flush Customer / Conversation / optional Order
    Chat-->>Adapter: deterministic reply
    Adapter->>DB: commit event and chat transaction
    Adapter-->>ManyChat: v2 Instagram text block
```

Evidence: `app/manychat.py::require_manychat_bearer()`, `manychat_request_key()`, and `receive_manychat_instagram()`. There is no outbound provider network call inside this handler; ManyChat receives the HTTP response and performs channel delivery. Failed events retain only a safe error type and may be retried.

## Flow-level Needs Verification

- **Needs Verification:** provider timeout budgets and production retry behavior are not configured in repository deployment assets; all shown outbound calls are currently in-process.

