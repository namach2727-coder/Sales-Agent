# AUDIT-01 — Repository Map

**Audit date:** 2026-07-20  
**Scope:** repository root, `app/`, `tests/`, `scripts/`, dependencies, `.env.example`, README, and existing docs. Secret values were not read or recorded.

## Application entry points

| Path and symbol | Current behavior |
|---|---|
| `app/main.py` — `app`, `lifespan()` | Full FastAPI MVP: creates tables, optionally seeds demo/catalog/module data, mounts static assets, and registers admin, connector, setup, legal, media, catalog, lead, order, and chat routes. README starts it with `python -m uvicorn app.main:app --reload`. |
| `app/public_instagram_gateway.py` — `app`, `lifespan()` | Reduced FastAPI app for Instagram webhook GET/POST, legal pages, and signed media only; OpenAPI/docs are disabled and safe access logging records method/path/status. |
| `app/telegram_polling.py` — `main()`, `run_polling()` | CLI polling loop that calls Telegram `getUpdates`, then delegates each update to `process_telegram_payload()`; started by `scripts/start_telegram.ps1` and `START_TELEGRAM_BOT.cmd`. |

## Main module map

| Repository path | Relevant symbols | Current behavior |
|---|---|---|
| `app/database.py` | `engine`, `SessionLocal`, `Base`, `get_db()` | Creates a synchronous SQLAlchemy engine/session factory from `Settings.database_url`; SQLite gets `check_same_thread=False`. |
| `app/models.py` | 25 `Base` subclasses | Defines all commerce, connector-event, catalog-version, content, module, store, audit, and Instagram-connection tables. |
| `app/schemas.py` | `ChatRequest`, `ChatResponse`, read/status schemas | Defines public request/response validation; a “lead” is a `Customer` with a saved phone, not a separate model. |
| `app/chat.py` | `process_chat()`, `build_reply()`, `handle_order()` | Deterministic Persian/Finglish engine for product/FAQ lookup, phone capture, pending order creation, and human-handoff flagging. |
| `app/catalog_text.py` | normalization/phrase helpers | Normalizes catalog/search text and phrase matching. |
| `app/catalog_runtime.py` | `resolve_product()`, `list_products()`, `find_knowledge_answer()` | Reads a store's active published knowledge version; the historical default store can fall back to the global demo catalog. |
| `app/catalog_training.py` | draft/analyze/publish functions | Creates reviewed catalog drafts and publishes versioned categories, products, aliases, and knowledge for the default store workflow. |
| `app/admin.py` | `require_local_admin()`, admin handlers | Serves the local-only manager console and catalog/test operations. |
| `app/admin_content.py` | content/media route handlers | Local-only product-image, deterministic social-copy, review, approval, and guarded Instagram-publish operations. |
| `app/admin_modules.py` | marketplace/provider handlers | Local-only store creation, module entitlement changes, and provider catalog price updates. |
| `app/module_catalog.py` | `module_enabled()`, `store_for_instagram_account()` | Seeds module definitions, evaluates store entitlements/dependencies, and maps Instagram accounts to stores. |
| `app/tenancy.py` | `parse_tenant_slug()`, `tenant_store_from_request()` | Parses configured subdomains and can resolve a store; no route currently calls `tenant_store_from_request()`. |
| `app/instagram.py` | parsers, `InstagramClient`, webhook handlers | Verifies Meta signatures, deduplicates text messages/comments, runs deterministic chat, and sends synchronous Graph API replies. |
| `app/instagram_publishing.py` | `InstagramContentPublisher`, `publish_content_draft()` | Publishes an approved single image through Meta's container/publish flow and stores an idempotent publish job/media mapping. |
| `app/telegram.py` | `TelegramClient`, parser/process/webhook functions | Accepts private text updates, deduplicates, runs deterministic chat, and sends replies or simulates sending. |
| `app/manychat.py` | `receive_manychat_instagram()` | Bearer-protected ManyChat Dynamic Block adapter returning a version-2 Instagram text response. |
| `app/media_storage.py` | JPEG save/resolve/sign functions | Validates and stores manager-uploaded JPEGs on local disk and creates expiring HMAC-signed public URLs. |
| `app/content_generation.py` | `generate_social_copy()`, draft lifecycle | Generates deterministic caption/hashtags/alt text/sales keywords and manages review state. |
| `app/*_setup.py` | local setup guards/save handlers | Development-loopback pages write Meta or Telegram settings to local `.env` without returning secrets. |
| `app/static/` | HTML/CSS/JavaScript | Persian RTL demo, local admin/content/module consoles, setup pages, and legal pages; no frontend build system is present. |

## Configuration and credential sources

`app/config.py` — `Settings` reads the root `.env` using `SettingsConfigDict`; `.env.example` documents names/default placeholders. `app/instagram_setup.py`, `app/telegram_setup.py`, and `scripts/configure_telegram.ps1` can write selected local `.env` values. The actual `.env` was not inspected.

| Environment name | `Settings` field | Reader/consumer |
|---|---|---|
| `DATABASE_URL` | `database_url` | `app/database.py`; SQLAlchemy engine |
| `META_VERIFY_TOKEN` | `meta_verify_token` | `app/instagram.py`; webhook challenge validation |
| `META_ACCESS_TOKEN` | `meta_access_token` | `app/instagram.py`, `app/instagram_publishing.py`; Meta outbound calls |
| `META_APP_SECRET` | `meta_app_secret` | `app/instagram.py`; webhook HMAC verification |
| `META_IG_USER_ID` | `meta_ig_user_id` | Instagram messaging/publishing and default store mapping |
| `MEDIA_SIGNING_SECRET` | `media_signing_secret` | `app/media_storage.py`; signed image links |
| `TELEGRAM_BOT_TOKEN` | `telegram_bot_token` | `app/telegram.py`; Bot API URLs |
| `TELEGRAM_WEBHOOK_SECRET` | `telegram_webhook_secret` | `app/telegram.py`; webhook header validation |
| `MANYCHAT_DYNAMIC_BLOCK_SECRET` | `manychat_dynamic_block_secret` | `app/manychat.py`; bearer validation |
| `OPENAI_API_KEY` | `openai_api_key` | Read only by `Settings`; no current LLM/OpenAI consumer found. |

Non-secret operational settings include app/seed mode, Meta API/send/signature/publish flags, media base/root, tenant domain/scheme, and Telegram send/poll settings.

## Tests, scripts, dependencies, and runtime artifacts

- `tests/` contains ten test modules plus `tests/conftest.py`; coverage areas are documented in `06-test-baseline.md`.
- `scripts/configure_telegram.ps1` securely prompts for a bot token and writes Telegram settings; `scripts/start_telegram.ps1` runs `app.telegram_polling` with the existing virtual environment.
- `requirements.txt` pins FastAPI, Uvicorn, SQLAlchemy, pydantic-settings, pytest, and httpx; no LLM, speech, audio, vector, or task-queue dependency is listed.
- Existing architecture documentation is `docs/blueprint/AI-Commerce-Platform-Blueprint.md`.
- Runtime/generated paths visible at root: `.venv/`, `.pytest_cache/`, `logs/`, `private_media/`, `sales_assistant.db`, two test `.db` files, `.env`, and Python cache patterns. `outputs/`, `work/`, `test_temp_run/`, `.codex-test-temp-*`, and `tools/` also exist; their intended ownership/lifecycle is **Needs Verification**.

## Needs Verification

1. **Needs Verification:** no repository script or deployment manifest shows how `app.public_instagram_gateway:app` is launched outside tests.
2. **Needs Verification:** `StoreInstagramConnection` has ciphertext/key/expiry columns, but repository searches found no encryption/decryption consumer; actual credential-population intent is unclear.
3. **Needs Verification:** `OPENAI_API_KEY` is documented/configured but unused; whether it is reserved or obsolete is not stated outside the blueprint.

