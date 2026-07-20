# AUDIT-02 — Route Exposure and Trust Boundaries

## طبقه‌بندی routeها

عبارت «فعلی» فقط رفتار کد است؛ local loopback هویت کاربر نیست و module gate مجوز کاربر نیست.

| routeها | guard و فرض فعلی | مرز هدف | auth / authorization / tenant | توصیه production |
|---|---|---|---|---|
| GET /، /demo، /static/{path} | بدون guard؛ demo عمومی | public static یا test/demo | هیچ؛ فایل‌ها نباید داده tenant داشته باشند | demo را از deployment اصلی حذف یا feature-flag کنید. |
| GET /privacy، /data-deletion | بدون guard | public legal | هیچ | عمومی بماند؛ محتوای حقوقی version شود. |
| GET /health | بدون guard؛ نام و environment برمی‌گرداند | internal health/operations | شبکه/ingress داخلی؛ tenant ندارد | پاسخ public فقط liveness حداقلی، readiness داخلی. |
| GET /products، /faqs | بدون auth؛ default/legacy | public tenant storefront یا authenticated store API طبق تصمیم محصول | host TenantContext؛ فقط catalog منتشرشده | API فعلی تا tenant-aware شدن externally exposed نباشد. |
| POST /chat | بدون auth؛ caller شناسه مشتری می‌دهد؛ default store | public tenant storefront | TenantContext از host/session؛ abuse control؛ customer identity از channel نه body آزاد | rate limit، size limit، correlation؛ store اجباری. |
| GET /leads، /orders | بدون guard و query سراسری | authenticated store API | user auth + membership + sales_operator/manager + store filter | فوراً از ingress عمومی مسدود شود. |
| GET /admin، /admin/api/state، /admin/api/content-studio | development+loopback/local host | authenticated store console | session auth، membership، viewer یا حوزه مربوط، TenantContext session/subdomain | local guard فقط development باقی بماند. |
| POST/PUT /admin/api/drafts/*، /admin/api/test | local mutation + same-origin/fetch-site | authenticated store API | catalog_editor؛ CSRF؛ tenant-bound draft | ID-only lookup ممنوع؛ test agent rate/retention محدود. |
| POST/GET/DELETE /admin/api/products/{id}/media و /product-media/{id}/* | local guard + module؛ بعضی lookupها ID-only | authenticated store API؛ preview خصوصی | catalog/content permission + TenantContext + record ownership | preview با session یا signed purpose-bound URL؛ IDOR test. |
| POST/PUT /admin/api/content-drafts/* و approve/publish | local guard + module/revision؛ draft lookup ID-only | authenticated store API | content_creator/reviewer/publisher تفکیک‌شده؛ tenant ownership | separation of duties اختیاری؛ publish audit اجباری. |
| GET /admin/api/module-marketplace?store_slug | local read؛ slug client | store console یا provider API | store member فقط store خودش؛ provider roles برای هر store | slug به‌تنهایی authority نباشد. |
| GET/POST /admin/api/provider/stores، PATCH provider stores/{slug}/modules/{code} و module-catalog/{code} | local guard | authenticated provider API | provider_admin/support با permission دقیق؛ explicit_internal TenantContext برای target | روی domain/ingress جدا، audit actor و step-up برای قیمت/billing. |
| GET /instagram/status، /telegram/status | بدون auth؛ فقط boolean/config readiness | internal health/operations | provider support auth؛ tenant/connection صریح | از public gateway حذف؛ پاسخ per-store حداقلی. |
| GET/POST /instagram/setup و POST /instagram/setup/verify-token؛ GET/POST /telegram/setup | development+loopback، origin/fetch-site و nonce یک‌بارمصرف | must not be externally exposed در شکل فعلی | production connector onboarding با user auth، owner/admin role، re-auth/CSRF، tenant | setup محلی را dev-only نگه دارید؛ secret را در UI/log برنگردانید. |
| GET /webhooks/instagram | verify token challenge | public provider webhook | request authenticity با verify token؛ account mapping در challenge محدود است | endpoint عمومی لازم است؛ rate limit و امن نگه‌داشتن token. |
| POST /webhooks/instagram | HMAC که با config قابل غیرفعال شدن است | public provider webhook | signature اجباری + connector-derived TenantContext + dedupe | در production bypass ناممکن؛ unknown account رد/ثبت امن. |
| POST /webhooks/telegram | secret header سراسری | public provider webhook | per-connection secret یا مسیر اختصاصی، connector TenantContext | global default ممنوع؛ secret rotation overlap. |
| POST /integrations/manychat/instagram | bearer سراسری | public provider webhook | per-connection secret + page/account binding + TenantContext | bearer نباید دسترسی همه storeها بدهد. |
| GET /media/publish/{asset_id} | HMAC+expiry، asset ready؛ URL replayable | public signed media | signature purpose/store/asset/version، expiry؛ tenant session لازم نیست | TTL کوتاه، key rotation، revoke/version و access log. |
| /docs، /openapi.json، /redoc، /docs/oauth2-redirect | FastAPI بدون auth در app اصلی؛ gateway خاموش | local-development only یا authenticated provider docs | provider auth/network allowlist | production به‌صورت پیش‌فرض disabled. |

Public Instagram gateway فقط webhook اینستاگرام، legal و signed media دارد و docs خاموش است؛ اما handlers/credentials مشترک همچنان isolation را حل نمی‌کنند.

## مدل اعتماد

Authentication هویت را ثابت می‌کند؛ authorization اجازه actor روی منبع را؛ request authenticity منشأ webhook را؛ tenant resolution حساب/host/session را به Store می‌بندد؛ entitlement قابلیت خریداری‌شده است؛ origin/nonce کنترل CSRF و loopback فقط trust محلی است.
