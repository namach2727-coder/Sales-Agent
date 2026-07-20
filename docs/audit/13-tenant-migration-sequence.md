# AUDIT-02 — Reversible Tenant Migration Sequence

## اصل اجرا

توالی زیر MVP را حفظ می‌کند؛ migration SQL ارائه نمی‌شود. dual-read/write نیازمند reconciliation است و داده مبهم quarantine می‌شود.

| فاز | هدف و فایل‌های اصلی | ریسک داده / rollback | پیش‌نیاز، تست و شرط تکمیل |
|---|---|---|---|
| 1. Freeze baseline | ثبت رفتار app/chat، connectors و اسناد AUDIT؛ tests | بدون تغییر داده؛ rollback ندارد | تست محدود 82-test یا baseline جدید green؛ fixtureهای tenant منفی طراحی شوند. |
| 2. Migration framework | افزودن ابزار versioned schema کنار app/database/models در task بعدی | خطر اجرای schema ناسازگار؛ rollback با downgrade آزمایش‌شده و backup | تصمیم DB production؛ empty DB و clone داده upgrade/downgrade شود؛ create_all دیگر منبع production نباشد. |
| 3. Canonical default Store | تثبیت یک default معتبر و mapping رکوردهای legacy | duplicate default/slug؛ rollback با mapping report | inventory و backup؛ job idempotent؛ دقیقاً یک default و شمارش مبنا ثبت شود. |
| 4. Nullable ownership | افزودن nullable store_id/connection_id به Product/FAQ/Customer/Conversation/Order/events و actor fields audit | writeهای قدیمی null می‌سازند؛ feature flag schema-only rollback | framework؛ app قدیمی با schema جدید کار کند؛ index اولیه بدون lock مخرب. |
| 5. Backfill | نسبت دادن legacy قطعی به default و connector events با account/page mapping | انتساب اشتباه؛ rollback با provenance/batch marker | canonical mapping؛ شمارش قبل/بعد، orphan و ambiguous report؛ ambiguous quarantine. |
| 6. Tenant-aware indexes/UQ | ایجاد index و uniqueness مرکب، آماده‌سازی FKهای سازگار | collisionهای فعلی؛ rollback index | dedupe plan؛ duplicate report صفر یا resolved؛ load/query plan قابل قبول. |
| 7. TenantContext plumbing | تعریف context immutable در tenancy و عبور از route→service→audit | رفتار ناخواسته fallback؛ rollback با compatibility adapter default فقط demo | هیچ enforcement داده هنوز؛ unit test چهار resolution source، unknown/inactive/ambiguous. |
| 8. Tenant-aware new writes | chat، catalog_training، connector handlers، content/publish همه owner را بنویسند | dual-write mismatch؛ rollback با flag و ستون nullable | Context حاضر؛ metric null write صفر در production shadow؛ parent ownership assertion tests. |
| 9. Tenant-filtered reads | main/chat/admin_content/catalog/connectors query را با store محدود کنند | رکورد backfill‌نشده پنهان می‌شود؛ rollback read flag و reconciliation | null/mismatch صفر؛ cross-tenant negative tests، parity count default. |
| 10. Identity و membership | User، Membership، session و actor audit contract | lockout کاربران؛ rollback local admin فقط در development | Product تصمیم auth provider؛ login/session/revoke tests؛ حداقل owner bootstrap. |
| 11. Protect routes/RBAC | dependency auth، permission و object-level checks؛ leads/orders/admin/provider split | اختلال workflow؛ rollback route-by-route flag، نه public bypass | permission matrix مصوب؛ anonymous/role/cross-store/CSRF tests؛ ingress policy. |
| 12. Per-store connector credentials | connection credential encryption/reference، expiry و rotation؛ Instagram سپس Telegram/ManyChat | ارسال از حساب غلط یا قطع ارسال؛ rollback dual-read به global فقط برای default | KMS/secret store و onboarding design؛ outbound mock تطبیق account/token، rotation/revoke tests. |
| 13. Disable unsafe fallbacks | حذف production default از process_chat/catalog/store_for_instagram؛ signature bypass ممنوع | channel بدون mapping fail می‌شود؛ rollback محدود با emergency flag و alert | تمام connectorها mapped؛ unknown traffic measured؛ fail-closed/no-side-effect tests. |
| 14. Enforce non-null/integrity | store_id/connection_id NOT NULL، FK/ownership constraints و UQ نهایی | lock و orphan failure؛ rollback constraint طبق runbook، نه حذف داده | null/orphan/mismatch صفر، backup و maintenance plan؛ migration clone موفق. |
| 15. Production hardening | secret rotation، rate limits، internal status/docs، backup/restore، retention، monitoring و incident runbook | operational regression؛ rollback config/version | security review، restore drill، alert tests، SLO و owner مشخص؛ approval production readiness. |

## ترتیب داخلی هر فاز

هر فاز observe-only، default canary، tenant مصنوعی دوم و rollout محدود دارد. write پیش از read enforcement می‌آید؛ constraint پس از reconciliation و صفر شدن mismatch؛ publish نزدیک network call account assertion می‌کند.

## تصمیم‌های لازم از Product Owner

1. Product per-store است یا catalog مشترک با offer/price فروشگاه؟
2. products/faqs storefront عمومی‌اند یا console API؟
3. support چه PII می‌بیند و break-glass چگونه تأیید می‌شود؟
4. سقف connection هر store چیست؟
5. retention مشتری، مکالمه، سفارش، connector event و audit چیست؟
6. نقش‌ها fixed هستند و separation تولید/تأیید/انتشار اجباری است؟
7. IdP و MFA owner/provider چیست؟
8. رفتار webhook/read/publish در suspend چیست؟

## کوچک‌ترین task اجرایی پیشنهادی

اول «TenantContext contract + تست resolution بدون تغییر schema» انجام شود: host/connector/session placeholder/explicit_internal، fail-closed، correlation ID و منع override از body/query/header. این task reversible و پیش‌نیاز migrationهاست و رفتار default MVP را تغییر نمی‌دهد.

Implementation پس از تأیید مالکیت، route boundary، RBAC، credential scope و تصمیم‌های Product شروع شود. store دوم تا بستن Criticalها، read/write tenant-aware، credential per-store و identity/membership مجاز نیست.
