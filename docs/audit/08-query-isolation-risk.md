# AUDIT-02 — Query Isolation and Tenant Context Risk

## queryهای پرریسک مبتنی بر شواهد

| شدت | فایل / تابع | الگوی فعلی و predicate مفقود | سناریو و مرز هدف |
|---|---|---|---|
| Critical | app/chat.py::process_chat | Customer با instagram_user_id؛ بدون store_id | یک شناسه در دو فروشگاه به یک پروفایل/تلفن تبدیل می‌شود. lookup و create باید با TenantContext.store_id + channel + external ID باشد. |
| Critical | app/chat.py::find_recent_product | Conversation فقط با customer_id | پیام فروشگاه A برای تشخیص محصول در B استفاده می‌شود. store_id و customer متعلق به همان tenant لازم است. |
| Critical | app/chat.py::handle_order | Order با customer_id/product_id/status؛ بدون store | pending order فروشگاه دیگر duplicate یا قابل بازگشت می‌شود. همه parentها و Order.store_id باید tenant-bound باشند. |
| Critical | app/main.py::list_leads/list_orders | select سراسری Customer/Order، بدون auth و tenant | هر caller همه PII و سفارش‌ها را می‌بیند. identity+membership+store predicate اجباری. |
| High | app/main.py::list_products/list_faqs و app/chat.py::find_faq_answer | default catalog و FAQ سراسری | کاتالوگ/پاسخ فروشگاه اشتباه افشا می‌شود. TenantContext و فقط نسخه فعال همان store. |
| High | app/instagram.py::DM event lookups | InstagramEvent.message_id تنها | dedupe بین connectionها collide می‌کند. connection_id + provider event ID. |
| High | app/instagram.py::comment lookup و app/instagram_publishing.py::mapping | CommentEvent.comment_id و MediaProduct.media_id تنها | comment به محصول یا reply فروشگاه دیگر وصل می‌شود. connection/store predicate در همان query. |
| High | app/telegram.py::process_telegram_payload | update_id تنها؛ process_chat بدون store_slug | همه Telegram در default ادغام می‌شود. اتصال verified باید TenantContext بسازد. |
| High | app/manychat.py::receive_manychat_instagram | request_key سراسری؛ process_chat default | bearer مشترک page را authorize نمی‌کند. secret/connection باید page را به store bind کند. |
| High | app/admin_content.py::_asset_or_404/_draft_or_404 | db.get/ID تنها؛ preview/delete/edit/approve | با admin واقعی، IDOR cross-store ممکن است. lookup باید (store_id,id) باشد؛ module gate authorization رکورد نیست. |
| High | app/catalog_training.py::update_training_draft/publish_training_draft | draft_id تنها | مدیر tenant می‌تواند draft tenant دیگر را mutate/publish کند. store predicate قبل از load. |
| Medium | app/public_media.py::public_product_image | asset_id + global HMAC؛ بدون store/connection | URL تا انقضا replay می‌شود؛ tenant revocation ندارد. signature باید purpose/store/version را bind کند یا URL یک‌بارمصرف/کوتاه باشد. |
| Medium | app/admin_modules.py::module_marketplace | store_slug از query با local guard، بدون membership | در production دانستن slug کافی خواهد بود. provider role یا membership همان store لازم است. |
| Medium | app/catalog_runtime::_active_version_id | slug دریافت‌شده؛ مالکیت version validate می‌شود؛ default fallback legacy | بخش managed خوب است، ولی default/فقدان store به Product سراسری برمی‌گردد. در production store صریح و active لازم است. |
| Medium | app/content_generation.py::default_store و admin content state | slug ثابت default | عملیات هر host روی default اجرا می‌شود. با TenantContext جایگزین شود. |

## وضعیت tenant resolution

- parse_tenant_slug میزبان را normalize می‌کند؛ localhost در development به default و subdomain معتبر به slug تبدیل می‌شود. این تابع identity یا authorization نیست.
- tenant_store_from_request از host، Store را می‌یابد و deleted/disabled را 404 می‌کند؛ هیچ route فعلی آن را dependency نکرده است.
- store_for_instagram_account اتصال active را با ig_user_id می‌یابد؛ اگر نبود، meta_ig_user_id سراسری را به default fallback می‌دهد. status خود Store در این تابع رد نمی‌شود، هرچند module_enabled حالت suspended/disabled/deleted را می‌بندد.
- module_enabled entitlement، زمان، dependency و lifecycle محدود Store را کنترل می‌کند؛ feature entitlement است، نه auth.
- catalog_runtime مالکیت active_version_id را با KnowledgeVersion.store_id بررسی می‌کند. برای non-default بدون نسخه fallback نمی‌کند؛ برای default می‌تواند به Product/FAQ legacy برگردد.
- فقط Instagram DM/comment store را از account می‌گیرد. Web chat، Telegram، ManyChat، admin catalog/content و APIهای اصلی عملاً default هستند. provider module route store_slug صریح می‌پذیرد.

## قرارداد حداقلی TenantContext

    {
      "store_id": 0,
      "store_slug": "...",
      "store_status": "active",
      "resolution_source": "subdomain|connector|session|explicit_internal",
      "actor": {"id": null, "type": "user|connector|system", "role": null},
      "membership_id": null,
      "connector": {"type": null, "connection_id": null, "account_id": null},
      "correlation_id": "...",
      "resolved_at": "...",
      "is_default_fallback": false
    }

Context فقط در boundary معتبر ساخته و immutable حمل شود؛ explicit_internal فقط برای سرویس مورد اعتماد است. store/connection باید مجاز و actor عضو همان store باشد. client نباید store را override کند.

## فهرست وابستگی default

| نماد | رفتار / علت | راهبرد |
|---|---|---|
| ensure_default_store در lifespan، catalog training، provider helper | bootstrap MVP و seed | برای demo نگه‌دار؛ production provisioning صریح. |
| process_chat و توابع catalog با store_slug=default | سازگاری API قدیمی | TenantContext اجباری؛ fallback فقط test/demo. |
| catalog_runtime fallback به Product/FAQ | catalog legacy | پس از backfill حذف؛ non-default هرگز fallback نکند. |
| content_generation.default_store و admin_content | کنسول محلی تک‌فروشگاهی | با session-derived TenantContext جایگزین. |
| Telegram/ManyChat | اتصال tenant ندارند | connection registry اجباری؛ unknown رد شود. |
| store_for_instagram_account fallback سراسری | سازگاری Meta setup فعلی | بعد از انتقال credential حذف؛ unknown account بدون side effect. |
