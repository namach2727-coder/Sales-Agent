# AUDIT-02 — Tenant Ownership Gap

هسته چندفروشگاهی ناقص است: نسخه دانش، ماژول‌ها و محتوا store-owned هستند؛ اما Product/FAQ، فروش و بیشتر رخدادهای connector سراسری‌اند.

## طبقه‌بندی همه مدل‌های ماندگار

در ستون «کلید فعلی»، مسیر غیرمستقیم با فلش نشان داده شده است. UQ یعنی قید یکتایی فعلی/هدف.

| مدل | مالکیت فعلی → هدف | کلید فعلی / کلید مفقود | UQ فعلی → هدف | ریسک، backfill و نگهداری |
|---|---|---|---|---|
| Product | سراسری → store-owned | ندارد / store_id | ندارد → (store_id, external_key یا normalized_name) | Critical؛ قیمت یک فروشگاه ممکن است در فروشگاه دیگر دیده شود. هر محصول legacy به default نسبت داده و حذف فروشگاه باید soft-delete/retain سفارش را رعایت کند. |
| FAQ | سراسری → store-version-owned | ندارد / knowledge_version_id یا store_id | question → نسخه+عنوان | High؛ پاسخ مشترک ناخواسته. داده legacy وارد نسخه default شود؛ نسخه‌های منتشرشده immutable نگه داشته شوند. |
| Customer | customer بدون tenant → customer-owned within store | ندارد / store_id | instagram_user_id → (store_id, channel, external_user_id) | Critical؛ هویت و تلفن بین فروشگاه‌ها ادغام می‌شود. backfill از رخداد/کانال و در موارد مبهم quarantine؛ حذف/ناشناس‌سازی تابع retention فروش باشد. |
| Conversation | customer-owned ناقص → customer-owned within store | customer_id / store_id دفاعی | ندارد → index(store_id, customer_id, created_at) | Critical؛ تاریخچه اخیر مرز فروشگاه ندارد. از Customer/connector backfill؛ متن دارای PII نیازمند retention است. |
| Order | customer-owned ناقص → store-owned + customer within store | customer_id, product_id / store_id | ندارد → tenant-aware idempotency/pending key | Critical؛ سفارش و قیمت اشتباه. از customer/product فقط پس از رفع ابهام backfill؛ سوابق مالی حذف نشوند و anonymize شوند. |
| InstagramEvent | connector سراسری → connector-owned within store | recipient_id / store_id, connection_id | message_id → (connection_id, message_id) | High؛ collision یا retry فروشگاه دیگر. backfill با recipient_id؛ payload/error retention محدود. |
| InstagramMediaProduct | connector سراسری → connector-owned within store | media_id, product_id / store_id, connection_id | media_id → (connection_id, media_id) | High؛ comment به محصول غلط وصل می‌شود. از حساب ناشر/job backfill؛ با حذف محصول mapping تاریخی retain/disable شود. |
| InstagramCommentEvent | connector سراسری → connector-owned within store | ig_account_id / store_id, connection_id | comment_id → (connection_id, comment_id) | High؛ dedupe و پاسخ cross-store. از ig_account_id backfill؛ متن comment retention محدود. |
| InstagramCommentPublicReply | connector سراسری → connector-owned within store | comment_id / store_id, connection_id | comment_id → (connection_id, comment_id) | High؛ پاسخ عمومی فروشگاه اشتباه. از CommentEvent backfill؛ سابقه عملیات retain شود. |
| TelegramEvent | connector سراسری → connector-owned within store | chat_id/update_id / store_id, connection_id | update_id → (connection_id, update_id) | High؛ Telegram فعلاً default است. تا ایجاد StoreTelegramConnection همه رکوردها default؛ retention متن/خطا محدود. |
| ManyChatEvent | connector سراسری → connector-owned within store | page_id/request_key / store_id, connection_id | request_key → (connection_id, request_key) | High؛ secret مشترک و page بدون tenant. backfill page_id→connection؛ response cache retention محدود. |
| Store | platform-global | id, slug | slug → بدون تغییر | Low؛ active_version_id باید FK/ownership-safe شود؛ حذف نرم و lifecycle کنترل‌شده. |
| TrainingDraft | store-owned → store-owned | store_id | ندارد | Medium IDOR؛ UQ لازم نیست، ولی تمام lookupها store_id بخواهند. draftهای قدیمی retention/archival. |
| KnowledgeVersion | store-owned → store-version-owned | store_id | (store_id, version_number)، source_draft_id global | Low؛ source draft باید همان store باشد. نسخه منتشرشده immutable و retain. |
| ProductCategory | version-owned → store-version-owned | version→store | (version, normalized_name) | Low؛ traversal کافی است، ولی query باید version فعال tenant را الزام کند؛ cascade با نسخه. |
| CatalogProduct | version-owned → store-version-owned | version→store؛ product legacy | (version, external_key)، (version, product_id) | Medium؛ Product سراسری مرز را تضعیف می‌کند. پس از tenant کردن Product، سازگاری store FKها enforce؛ snapshot retain. |
| ProductAlias | version/product-owned → store-version-owned | catalog_product→version→store | (catalog_product, normalized_value) | Low؛ lookup فقط در نسخه فعال tenant؛ cascade با catalog product. |
| KnowledgeItem | version-owned → store-version-owned | version→store | (version, kind, title) | Low؛ query صحیح به version وابسته است؛ نسخه retain. |
| AdminAuditLog | audit store-owned → audit/operational | store_id / actor_id, correlation_id | ندارد → index(store_id,timestamp) | High accountability؛ actor موجود نیست. append-only با retention قانونی. |
| ProductMediaAsset | store-owned | store_id، product_id legacy | storage_key global → storage_key global و hash/index tenant-aware | High IDOR؛ product باید همان store باشد. فایل‌ها بعد از grace period پاک شوند، metadata audit باقی بماند. |
| SocialContentDraft | store-owned | store_id؛ product/media IDs | ندارد → index(store_id,status,updated_at) | High IDOR؛ FKهای وابسته باید همان store باشند. نسخه‌های approved/published retain. |
| InstagramPublishJob | audit/operational store-owned | store_id, draft_id | draft_id و idempotency_key global | Medium؛ ownership draft باید enforce شود. سوابق publish برای reconciliation retain. |
| ModuleDefinition | platform-global | code | PK code | Low؛ provider-managed، حذف فقط deprecate تا entitlementها معتبر بمانند. |
| StoreModule | store-owned | store_id | (store_id,module_code) | Low؛ ساختار درست است؛ actor/billing source نیاز دارد. سوابق entitlement retain. |
| StoreInstagramConnection | connector-owned within store | store_id | store_id global unique، ig_user_id global unique | Medium؛ یک حساب برای یک store مناسب است، ولی token fields بلااستفاده‌اند. اتصال revoke‌شده و تاریخچه rotation باید audit شود. |

## قواعد مالکیت هدف

مالکیت مستقیم روی داده عملیاتی پرخطر الزامی است؛ traversal فقط برای داده immutable نسخه‌ای کافی است. parent و child باید یک store داشته باشند و شناسه خارجی به‌تنهایی TenantContext نیست.
