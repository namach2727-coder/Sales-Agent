# AUDIT-02 — Security and Tenant Risk Register

## رتبه‌بندی

| ID / شدت | عنوان و دامنه | سناریو؛ کنترل فعلی / کنترل مفقود | اصلاح، وابستگی و آزمون |
|---|---|---|---|
| TIR-01 Critical | Customer cross-store؛ models.py، chat.process_chat | external user ID سراسری تلفن/نام را ادغام می‌کند؛ unique global / store key ندارد | store_id و UQ tenant-aware؛ وابسته به TenantContext؛ دو store با ID یکسان باید دو customer بسازند. |
| TIR-02 Critical | Conversation cross-store؛ chat.find_recent_product | تاریخچه customer سراسری محصول قبلی را به store دیگر می‌برد؛ customer FK / store predicate ندارد | store_id و filtered reads؛ تست پیام A در B هرگز context محصول نسازد. |
| TIR-03 Critical | Order cross-store؛ chat.handle_order، main /orders | سفارش/duplicate سراسری و endpoint بدون auth؛ parent FK / tenant+identity ندارد | Order.store_id، service authorization و endpoint guard؛ کاربر B نتواند order A را ببیند/اثر دهد. |
| TIR-04 Critical | Global Meta send identity؛ instagram.py، instagram_publishing.py | store از recipient resolve می‌شود ولی token/account از Settings سراسری است؛ module gate / credential pair per connection ندارد | per-store encrypted credential؛ آزمون mock URL/header دقیق برای دو store. |
| TIR-05 Critical | Unauthenticated leads/orders؛ main.py | هر caller همه PII/فروش را می‌گیرد؛ هیچ کنترل / user session+membership+role مفقود | از ingress مسدود سپس auth/RBAC/filter؛ anonymous=401 و cross-store=404. |
| TIR-06 High | Product/FAQ leakage؛ models، main، catalog_runtime/chat | default legacy fallback داده سراسری می‌دهد؛ managed version check / مالکیت legacy مفقود | backfill default، tenant product/knowledge، fallback production off؛ catalog هر tenant متفاوت تست شود. |
| TIR-07 High | Connector event collision؛ Instagram/Telegram/ManyChat models و handlers | provider ID/request key global retry store دیگر را duplicate می‌کند؛ UQ global / connection scope ندارد | connection_id + composite UQ؛ event مشابه در دو connection مستقل پردازش شود. |
| TIR-08 High | Wrong comment product/reply؛ instagram.py، InstagramMediaProduct | media_id تنها mapping است؛ account resolution موجود / store predicate مفقود | connection/store mapping و same-store product؛ comment B هرگز product A نگیرد. |
| TIR-09 High | IDOR رسانه/محتوا؛ admin_content.py | asset/draft با ID تنها؛ local guard/module / object ownership ندارد | query (store,id) و service invariant؛ ID tenant دیگر 404 و فایل untouched. |
| TIR-10 High | Missing user identity/membership؛ admin.py و همه admin routes | loopback دستگاه را trusted می‌داند؛ origin کمک CSRF / identity و membership وجود ندارد | session+User+Membership+deny-default؛ تست نقش‌ها و membership غیرفعال. |
| TIR-11 High | Unsafe default-store fallback؛ catalog/chat/module_catalog | unknown/implicit channel به default می‌رود؛ compatibility / fail-closed نیست | context اجباری و fallback demo-only؛ unknown account/host هیچ write نکند. |
| TIR-12 High | Configurable Meta signature bypass؛ instagram.verify_meta_signature | META_SIGNATURE_REQUIRED=false پذیرش unsigned؛ default true / production invariant ندارد | startup fail اگر production false؛ unsigned همیشه 401 و no event. |
| TIR-13 High | Local admin accidental exposure؛ admin/setup | app_env اشتباه یا proxy/client-host اعتماد؛ loopback+host / deployment isolation و real auth ندارد | route جدا/dev build، ingress deny و auth؛ production route 404 حتی با spoofed headers. |
| TIR-14 High | Credential lifecycle؛ config، setup، StoreInstagramConnection | tokens plaintext/global، token columns unused؛ redaction جزئی / encryption, expiry, rotation ندارد | secret manager+KMS+per connection؛ expiry/rotation/no-leak tests. |
| TIR-15 Medium | Status information exposure؛ /instagram/status، /telegram/status، /health | readiness و environment public؛ secret values مخفی / audience guard ندارد | internal/provider support؛ anonymous production 404 یا minimal. |
| TIR-16 Medium | Setup route exposure/CSRF boundary | nonce/origin/loopback خوب است؛ user auth و durable nonce store ندارد | dev-only؛ production onboarding authenticated+step-up؛ remote/origin/replay tests. |
| TIR-17 Medium | Signed media replay؛ public_media/media_storage | HMAC و expiry؛ URL تا expiry bearer است و key global / revoke, purpose, tenant binding ندارد | kid/key ring، short TTL و version/purpose binding؛ replay پس از revoke رد شود. |
| TIR-18 Medium | Missing audit actor؛ AdminAuditLog | store/action موجود؛ actor/session/correlation ندارد | append-only actor context؛ هر mutation audit قابل انتساب تست شود. |
| TIR-19 Medium | Store status inconsistency؛ module_catalog.store_for_instagram_account | active connection ممکن است store suspended بدهد؛ بعضی module gates بعداً / resolver fail-closed یکنواخت ندارد | resolver status policy؛ suspended connector قبل از DB business write رد شود. |
| TIR-20 Medium | active_version pointer integrity؛ Store/Catalog runtime | integer بدون FK است؛ runtime ownership check / DB integrity و atomic activation محدود | FK/transactional ownership validation در migration آینده؛ cross-store pointer هیچ catalog ندهد. |

## اولویت اقدام

Blocking فروشگاه دوم: TIR-01 تا 05، سپس 07/08/10/11/14. موقتاً deployment تک‌فروشگاهی، leads/orders غیرعمومی، بدون connector دوم و signature اجباری بماند.

هیچ penetration test در این audit اجرا نشد.
