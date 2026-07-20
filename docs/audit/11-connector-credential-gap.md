# AUDIT-02 — Connector Credential Gap

## موجودی credentialها

همه مقادیر زیر در app/config.py::Settings از محیط/.env خوانده می‌شوند و scope عملی فعلی‌شان process-global است. هیچ مقدار واقعی در این سند نمایش داده نشده است.

| credential | reader / consumer | rotation، persistence، encryption | ریسک و scope هدف |
|---|---|---|---|
| META_VERIFY_TOKEN | instagram.verify_instagram_webhook | setup آن را در .env بازنویسی و runtime را refresh می‌کند؛ rotation overlap/version ندارد؛ plaintext local | challenge همه storeها مشترک است. می‌تواند endpoint-level global بماند اگر Meta contract اجازه دهد، با secret manager و rotation؛ tenant را از account event resolve کنید. |
| META_APP_SECRET | instagram.verify_meta_signature | setup در .env؛ encryption app-level ندارد؛ rotation همزمان ندارد | request-authenticity کل app. production signature همیشه required و secret در managed secret store؛ rotation runbook. |
| META_ACCESS_TOKEN | InstagramClient، InstagramContentPublisher | setup در .env؛ token refresh/expiry check ندارد | Critical: پاسخ و publish همه storeها با یک token. باید per StoreInstagramConnection، encrypted at rest، decrypt فقط هنگام مصرف، expiry/refresh/revoke باشد. |
| META_IG_USER_ID | InstagramClient/Publisher URL، mapping fallback | .env و ensure_default_instagram_connection | Critical: store resolve شده ولی outbound account global است. هدف connection.ig_user_id همان TenantContext و credential pair باشد؛ fallback حذف. |
| TELEGRAM_BOT_TOKEN | TelegramClient و polling | setup با getMe verify و .env save؛ rotation/expiry/encryption ندارد | global/default. StoreTelegramConnection با token encrypted، bot/account unique و rotation لازم است. URL حاوی token است؛ کد فعلی از ذخیره exception URL پرهیز می‌کند. |
| TELEGRAM_WEBHOOK_SECRET | verify_telegram_secret | setup تولید/ذخیره local؛ shared global | request-authenticity دارد ولی tenant bind ندارد. per connection یا secret-version→connection، overlap rotation و constant-time compare. |
| MANYCHAT_DYNAMIC_BLOCK_SECRET | require_manychat_bearer | محیط فقط؛ bearer global، rotation/persistence/encryption ندارد | یک secret به همه pageها authority می‌دهد. per connection secret hash/encrypted reference، page_id binding و dual-secret rotation. |
| MEDIA_SIGNING_SECRET | create/validate_public_media_signature | محیط؛ HMAC global؛ rotation key ID ندارد | URL asset+expiry قابل replay تا حداکثر دو ساعت اعتبار ورودی و معمولاً یک ساعت تولیدی. key ring با kid، purpose/store/asset/version، TTL کوتاه و revocation. |

## بررسی StoreInstagramConnection

- ستون‌های token_ciphertext، token_key_id و token_expires_at در مدل وجود دارند.
- هیچ writer در مخزن این سه ستون را مقداردهی نمی‌کند؛ ensure_default_instagram_connection فقط store_id، ig_user_id و status را می‌نویسد.
- هیچ reader/consumer برای این ستون‌ها یافت نشد؛ ارسال DM/comment و انتشار همچنان Settings سراسری را مصرف می‌کند.
- encryption/decryption یا KMS/key-provider در مخزن وجود ندارد و expiry بررسی نمی‌شود.
- store_id و ig_user_id هر دو unique هستند؛ یک اتصال برای هر store و یک store برای هر حساب را enforce می‌کند.
- lookup فقط connection.status=active را می‌سنجد؛ status خود Store در store_for_instagram_account رد نمی‌شود. module_enabled بعداً برخی وضعیت‌ها را می‌بندد، اما این کنترل یکنواخت نیست.
- اگر connection یافت نشود و ig_user_id با META_IG_USER_ID برابر باشد، default Store برگردانده می‌شود. این fallback همراه با token outbound سراسری می‌تواند عملیات را به حساب نادرست ببرد.

## Target State و migration

Connection هدف باید store/account/status، credential ciphertext/reference، key_id، expiry، scopes و rotation version داشته باشد. plaintext فقط کوتاه‌عمر در حافظه، UI write-only و log redacted باشد. mapping را backfill، dual-read را اندازه‌گیری، سپس per-store مصرف و global fallback را خاموش کنید.
