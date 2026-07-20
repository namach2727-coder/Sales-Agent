# AUDIT-02 — Authentication and RBAC Gap

## وضعیت فعلی کنترل هویت

- require_local_admin و require_local_setup فقط development، loopback client و hostname محلی را می‌پذیرند؛ user identity، session، membership یا MFA ندارند.
- mutationهای admin/setup Origin و Sec-Fetch-Site را بررسی می‌کنند. setup nonce یک‌بارمصرف و کوتاه‌عمر است؛ این‌ها CSRF-style هستند، نه login.
- Meta HMAC، Telegram secret header و ManyChat bearer اصالت درخواست/connector را می‌سنجند. Meta signature می‌تواند با META_SIGNATURE_REQUIRED خاموش شود.
- URL رسانه با HMAC و expiry مجاز می‌شود؛ actor یا tenant membership را ثابت نمی‌کند.
- module_enabled وضعیت فروشگاه، entitlement، زمان و dependency را می‌سنجد؛ authorization کاربر نیست.
- AdminAuditLog store/action/entity دارد اما actor_id، role، IP/session و correlation_id ندارد.

## Target State

Identity provider/session باید cookie امن، CSRF، logout/revocation و MFA-ready claims بدهد. User و StoreMembership مرز اصلی‌اند؛ provider audience جداست و authorization در route و عملیات حساس تکرار می‌شود.

## نقش‌های حداقلی

- provider_admin: مدیریت platform، catalog ماژول، فروشگاه‌ها، billing و دسترسی اضطراری audit‌شده.
- provider_support: مشاهده محدود و impersonation/support موقت با reason؛ بدون تغییر قیمت یا credential مگر مجوز جدا.
- store_owner: اعضا، تنظیمات، connector و billing همان store.
- store_manager: عملیات روزمره و ماژول‌ها، بدون انتقال مالکیت/billing حساس.
- catalog_editor: محصول، alias، FAQ و draft catalog.
- content_creator / content_reviewer / content_publisher: تولید، تأیید و انتشار جدا.
- sales_operator: مشتری، lead، conversation، order و handoff.
- viewer: read-only غیرحساس بر اساس حوزه.

## ماتریس permission

P=provider_admin، S=provider_support، O=owner، M=manager، E=catalog_editor، C=creator، R=reviewer، U=publisher، X=sales_operator، V=viewer. «R» در خانه یعنی read و با نقش Reviewer اشتباه نشود.

| حوزه | مشاهده | تغییر/عمل حساس |
|---|---|---|
| store settings | P,S,O,M,V | P/O؛ M فقط تنظیم غیرامن |
| users/memberships | P,S,O | O؛ P فقط recovery؛ support بدون grant |
| products/catalog | P,S,O,M,E,V | O/M/E؛ publish catalog با E یا M |
| customers/leads | P,S,O,M,X | O/M/X؛ export permission جدا |
| conversations | P,S,O,M,X | O/M/X؛ پاسخ/assign |
| orders | P,S,O,M,X,V محدود | O/M/X؛ refund/payment جدا در آینده |
| content | P,S,O,M,C,R,U,V | C create/edit، R approve، U publish |
| publishing | P,S,O,M,U | U/O؛ credential و entitlement هر دو لازم |
| connectors | P,S,O,M | O؛ M فقط با connector_manage؛ secrets هرگز read-back |
| modules | P,S,O,M,V | P قیمت/catalog؛ O/M enable در قرارداد |
| billing | P,S,O | P/O؛ support read-only masked |
| audit logs | P,S,O و M محدود | append-only system؛ export P/O |

هر permission علاوه بر role به store membership، resource ownership و module entitlement وابسته است. provider_support دسترسی پیش‌فرض به PII ندارد و break-glass باید زمان‌دار و audit شود.

## MFA readiness

مدل session باید auth_time، amr/acr، MFA enrollment state و step-up timestamp را حمل کند. عملیات اعضا، connector secret، billing، publish و provider admin نیازمند step-up قابل تنظیم هستند. recovery code، device/session revocation و audit event از ابتدا در طراحی لحاظ شود؛ اجرای MFA می‌تواند مرحله بعد باشد.

## توصیه و معیار پذیرش

ابتدا User/Membership/session و permissionها، سپس read-only console و بعد mutationها پیاده شود. deny-by-default و object-level check لازم است. تست‌ها anonymous، نقش ناکافی، tenant دیگر، membership معلق، CSRF، session منقضی و audience اشتباه را پوشش دهند. هیچ slug/ID/loopback/entitlement به‌تنهایی authorization نیست؛ audit باید actor+store+correlation داشته باشد.
