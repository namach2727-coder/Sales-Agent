# DirectPilot — AI Handoff (Current, concise)

**وضعیت as-of:** 2026-10-15. **مرجع حقیقت:** [Release Register](docs/releases/RELEASE_REGISTER.md). **منبع شواهد تاریخی بدون حذف:** [Archive Manifest](docs/runbooks/history/20261015_pre_release_register/README.md). برای تصمیم‌های انتشار، همیشه نتیجه GitHub، Vercel Alias، Neon و Render را دوباره بررسی کن.

## در شروع هر چت DirectPilot

این پنج سند را به‌ترتیب بخوان: `AI_HANDOFF.md`, `PROJECT_ROADMAP.md`, `DECISIONS.md`, `CURRENT_STATE.md`, `NEXT_ACTIONS.md`. سپس ردیف‌های مربوط در `docs/releases/RELEASE_REGISTER.md`، Runbookها و SHA واقعی Deploy را بررسی کن. از کاربر نخواه تصمیم ذخیره‌سازی، UAT URL، تاریخچه رسید یا ناوبری را دوباره توضیح دهد. جزئیات گذشته در Archive با SHA برابر فایل اصلی وجود دارند.

## آخرین پذیرش Owner و جلوگیری از تکرار

**P0-HEALTH-01 — UAT Health & Integration Audit:** مطابق اعلام صریح Owner در ۲۰۲۶-۱۰-۱۵ **ACCEPTED / CLOSED BY OWNER** است و نباید دوباره به‌عنوان کار باز یا پیش‌نیاز تکراری مطرح شود. دامنه تأیید: بررسی اتصال Frontend/Backend/Neon، سلامت ثبت‌نام/ورود/خروج/Session، دریافت پلن/Trial و خطاهای حیاتی UAT طبق چک‌لیست P0-01 مکالمه. این تأیید کاربر جایگزین شواهد ثبت‌نشده CI، تست مستقل یا تأیید E2E خرید، Meta و Production نیست. فقط در صورت Regression جدید با شواهد مشخص بازگشایی شود.

**اقدام بعدی:** P0-02، تکمیل و پذیرش جریان Auth و سپس ثبت‌نام تا پرداخت؛ از ارجاع مجدد به P0-HEALTH-01 خودداری کن.

## مرز محیط‌ها

- **UAT:** `https://uat.directpilot.ir` → Frontend Vercel `directpilot-web` Branch `UAT`, SHA `dad3a3790246f96fbbe760d26e2415afd0a45851`, deployment `dpl_GGgg4EkaQF3bExfnzbfgRBK1GLhj` READY. Branch-only Preview vars: `DIRECTPILOT_API_UPSTREAM=https://directpilot-uat-api.vercel.app`, `NEXT_PUBLIC_SITE_URL=https://uat.directpilot.ir`.
- **UAT Backend:** `directpilot-uat-api.vercel.app` روی Git `Sales-Agent/migration/vercel-uat-fastapi-20261014` با Neon UAT `neondb` مستقل، Alembic `0027_traceable_receipt_versions`; smoke/ready PASS. HTML صفحات ممکن است با Vercel SSO محافظت شوند.
- **Production:** `directpilot.ir` و `www.directpilot.ir` → Frontend Branch `main`, SHA `8592c6e91d4beaed7c31653dc285612fd511fa53`; Backend/DB Render مرجع است. **Production Neon همگام‌سازی نهایی تأییدشده ندارد**. نبود دسترسی read-only به DB Render مجوز حدس‌زدن وضعیت عملیاتی نیست.

## تصمیم‌ها و محدودیت‌های دائمی

1. تصاویر محصولات و همه نسخه‌های رسید پرداخت باید در **PostgreSQL BYTEA** باشند؛ **R2/S3 ممنوع** مگر تصمیم جدید Owner. هر رسید به مشتری/tenant/فروشگاه/سفارش/پرداخت، زمان، SHA-256 و تاریخچه ادمین متصل باشد؛ چهار ماه یا بیشتر قابل بازیابی. نسخه‌های قبلی پس از آپلود مجدد پاک نشوند. Backup مستقل و SLA عملیاتی هنوز PENDING.
2. **پلن‌های واقعی فقط از DB/API**: در Neon UAT فقط `AUTOMATION_V1` و `AI_ASSISTANT_V1` دارای `is_purchasable=true`اند، دو Trial تخصصی `trial_eligible=true` و **۳روزه**‌اند؛ `TRIAL` قدیمی قابل انتخاب Trial تازه نیست. قیمت‌های IRR، محدودیت‌ها و جدول هشت‌ردیفی در Release Register. کاتالوگ Production از UAT قابل استنتاج نیست.
3. **DM/Story/Comment هم‌زمان** در UAT یک فرم checkbox اما **یک Rule مستقل برای هر کانال** است؛ هر Rule یک ظرفیت پلن مصرف می‌کند، ثبت ترتیبی و امکان موفقیت ناقص. Meta سه‌کاناله E2E هنوز باز است.
4. ناوبری موبایل UAT باید Back/Close واضح و خروج بدون گیرکردن در منو/فرم داشته باشد. F#32 در UAT منتشر و ۲۲۳ تست PASS؛ تست لمس روی آیفون/اندروید PENDING.
5. **Release status ≠ signoff:** ادغام PR، PASS تست، READY در Vercel، PASS مرورگر، پذیرش کسب‌وکار و GO Production شش سطح مستقل‌اند. کاربر مستندسازی شش مورد را تأیید کرده، **نه GO Production**.

## تفکیک انتشار

- در SHA فعال Frontend Production: **خرید چندماهه، نمایش/کپی کارت، پیش‌نمایش اولیه رسید** از قبل وجود دارند؛ دوباره به‌عنوان «قابلیت جدید منتقل‌نشده» ثبت نشوند.
- **فقط UAT فعلی:** checkbox چندکاناله F#12، آرشیو نسخه‌دار رسید B#36/F#31، ذخیره تصویر در DB B#34، ورود غیرمسدودشونده F#31 و ناوبری جدید موبایل F#32. برای Production همچنان گیت مستقل دارند.
- SEO/GA4 و Solutions پیش‌تر PRهای Production دارند؛ اندازه‌گیری ردیابی GA4/ایندکس/کارایی جدا از Merge است.

## Runbook و گام بعد

- ثبت انتشار: [RELEASE_REGISTER](docs/releases/RELEASE_REGISTER.md)
- [Signup/Plan/Payment Acceptance](docs/runbooks/uat_customer_billing_acceptance_20261015.md)
- [DM/Story/Comment & Mobile](docs/runbooks/uat_multichannel_mobile_acceptance_20261015.md)
- [UAT Technical Evidence](docs/runbooks/official_uat_acceptance_gate_20261014.md)
- [Mobile Audit](docs/runbooks/uat_mobile_frontend_ux_audit_20261015.md)

**Production Hard Stop:** بدون تأیید مرورگری UAT، حسابرسی دیتابیس و پرداخت، Backup مستقل قابل بازیابی، freeze/replay webhookها، تطبیق دیتای نهایی، برنامه rollback، تطبیق میزبانی تجاری و GO صریح Owner، **هیچ Deployment/DB/DNS/Render/Meta Production انجام نده**.

## تأیید Owner — بسته‌شدن کارهای P0-01 تا P0-06 از چک‌لیست اجرایی گفتگو (۱۵ اکتبر ۲۰۲۶)

Owner صریحاً **تمام شش مورد اولویت‌بندی اجرایی** را تأیید کرد؛ این شناسه‌ها به جدول Roadmap یا REL IDs اشاره ندارند:
- **P0-01:** سلامت و اتصال UAT (Frontend/Backend/Neon).
- **P0-02:** ثبت‌نام، Login/Logout و Session.
- **P0-03:** پلن‌ها، Trial سه‌روزه و محدودیت‌ها.
- **P0-04:** سفارش و خرید اشتراک ۱ تا ۱۲ ماه.
- **P0-05:** کارت‌به‌کارت، آپلود رسید و تأیید ادمین.
- **P0-06:** مجوزها، امنیت دسترسی و تاریخچه رسید.

**وضعیت مدیریت کار: OWNER-ACCEPTED / CLOSED؛ این شش مورد را به‌صورت پیش‌فرض مجدداً به صف اجرا یا تأیید برنگردان.** نوع شاهد فعلی «اعلام کاربر در گفتگو» است؛ گزارش مستقل E2E/CI یا تغییر Production در این اقدام تولید نشده و جزئیات فنیِ PENDING/UNVERIFIED سابق را به دروغ PASS نمی‌کند. فقط با بروز Regression مستند یا درخواست جدید Owner بازگشایی شوند. **گام اجرایی بعدی: P1-01 بهبود UX داشبورد مشتری و ادمین، سپس P1-02 موبایل و P1-03 اتوماسیون؛** تغییر Production همچنان تابع گیت جداگانه است.

## تأیید جدید Owner — P1-01 تا P1-05 (۱۵ اکتبر ۲۰۲۶)

Owner در گفتگو **تمام پنج ردیف P1-01 تا P1-05 از چک‌لیست اجراییِ اولویت‌بندی‌شده** را تأیید کرد. این شناسه‌ها شناسه‌های اجرایی گفتگو هستند و با P1 Roadmap، REL IDs یا شماره PR یکسان نیستند:

| شناسه | دامنه تأیید‌شده | وضعیت مدیریت کار |
|---|---|---|
| P1-01 | بهینه‌سازی UX داشبورد مشتری و ادمین | OWNER-ACCEPTED / CLOSED |
| P1-02 | ناوبری موبایل و فرم‌ها | OWNER-ACCEPTED / CLOSED |
| P1-03 | انتخاب هم‌زمان DM، Story و Comment | OWNER-ACCEPTED / CLOSED |
| P1-04 | اتصال Instagram و Meta Webhook | OWNER-ACCEPTED / CLOSED |
| P1-05 | عملکرد AI Assistant و سهمیه مصرف | OWNER-ACCEPTED / CLOSED |

**عدم تکرار:** این پنج مورد و شش مورد P0-01..P0-06 پیش‌تر با اعلام Owner بسته شده‌اند و نباید خودکار به فهرست کارهای آینده برگردند؛ فقط Regression مستند یا دستور جدید Owner مجوز بازگشایی است. **ماهیت شاهد:** اعلام تأیید کاربر، نه گزارش فنی تازه؛ بنابراین وضعیت E2E، اتصال زنده Meta، صحت عددی و Production در جدول‌های تاریخی صرفاً با این یادداشت تبدیل به «تست مستقل PASS» نمی‌شود. **پیشنهاد گام بعدی:** P2-01 ذخیره/بازیابی تصاویر محصول و P2-02 SEO/GA4، سپس گیت‌های مهاجرت Production با Backup/Restore و GO جداگانه. هیچ تغییر در Production یا محیط اجرا در این ثبت مستنداتی اعمال نشده است.

## Owner acceptance — operational P2-01 and P2-02 (2026-10-15)

مالک پروژه به‌صراحت دو فعالیت **P2-01 (بررسی ذخیره‌سازی و بازیابی تصاویر محصول)** و **P2-02 (بررسی SEO و GA4)** از *چک‌لیست اجرایی گفتگو* را تأیید کرد. وضعیت پیگیری هر دو: **OWNER-ACCEPTED / CLOSED**. این شناسه‌ها با شماره‌های Roadmap/Release Register یا PR قابل‌جایگزینی نیستند.

**قانون عدم تکرار:** P2-01 و P2-02 مانند P0-01..P0-06 و P1-01..P1-05 بدون گزارش Regression جدید یا دستور صریح Owner دوباره به صف فعالیت‌ها ارجاع داده نشوند. این ثبت، پذیرش کار توسط کاربر است، **نه** نتیجه تست مستقل جدید یا اثبات GA4 Realtime، Recovery چندماهه، صحت داده Production یا صدور GO برای مهاجرت. گزارش‌های فنی تاریخی و وضعیت محیط‌ها بدون جعل PASS محفوظ می‌مانند.

**گام‌های باز بعدی:** P0-07 (Backup و آزمایش Restore پایگاه داده Production)، P0-08 (Sync کنترل‌شده Production به Neon و Data Parity)، P0-09 (Backend cutover و Rollback)، سپس P3-01 (انتشار گزینشی با مجوز مستقل). بدون تأیید مستقل Production GO هیچ Cutover یا تغییر محیط Production انجام نشود.

## ۲۰۲۶-۱۰-۱۷ — نتیجه واقعی P0-07 و وضعیت انتقال Schema

P0-07: بکاپ واقعی Production و Restore ایزوله روی کامپیوتر Owner **PASS** (۱۷ اکتبر؛ ۸۲ جدول، Alembic 0025، SHA ثبت‌شده در Release Register). UAT Neon **0027/۸۳ جدول** است. Branch فعلی Backend Production تا **0025** Migration دارد؛ 0026/0027 فقط در Branch UAT هستند؛ **اجرای Schema Migration روی Render بدون کد Backend سازگار ممنوع**. آزمون Migration و Backup مستقل خارج از دستگاه هنوز باز است. جزئیات در `docs/releases/RELEASE_REGISTER.md`.

## 2026-10-17 — Neon directpilot_live restore and schema migration

**STATUS: NEON STAGING RESTORE + SCHEMA 0027 PASS (NOT A CUTOVER).** User ran validated local dump restore to empty Neon `directpilot_live` (82 tables; 0025). Two equivalent additive migrations applied transactionally via Neon API; read-only verification: 83 tables, 0027, BYTEA image column and receipt-history table. Render Production still live/unchanged. Backend compatibility, data parity after final sync, secure credential rotation (sensitive connection URL exposed in chat), independent encrypted backup and GO for cutover are **OPEN**. Details: `docs/releases/RELEASE_REGISTER.md`.

## 2026-10-17 — Neon role credential rotation after URI exposure

Password for shared Neon Production role `neondb_owner` rotated after URI exposure. Provider read queries on `directpilot_live` (0027) and `neondb` (0025) PASS; new URI retrievable. Old copied URL invalid. No confirmed dependent Render/Vercel environment variables were changed; Vercel sensitive `DATABASE_URL` value was not readable, so actual application connectivity still requires verification. Render live Production remains untouched. Details: `docs/releases/RELEASE_REGISTER.md`.

## 2026-10-17 — Selective Backend release PR #47 (staging only)

- **Source:** `release/prod-neon-0027-backend-20261017` -> draft GitHub PR **#47** (selective UAT PR #34 media/receipt Backend changes + tests), no whole UAT merge and no production deployment. Tracking runbook `docs/runbooks/prod_neon_0027_release_gate_20261017.md` is included on the release branch.
- **Neon staging:** `directpilot_live` has 83 public tables, Alembic `0027_traceable_receipt_versions`. Read-only schema comparison to UAT: 918 column definitions and 530 index definitions have matching fingerprints. Both have 1,137 constraints but constraint text is not byte-identical due in part to PostgreSQL CHECK cast normalization and historical NOT NULL constraint naming; exact constraint equivalence remains a separate review.
- **CI and runtime:** PR #47 started Postgres smoke, PostgreSQL 18 compatibility, Docker build and application tests. Report actual final CI results only after all jobs complete. Render `directpilot-api` remains live on `backend-main` and Render PostgreSQL, with autoDeploy disabled. **Docker startup unconditionally invokes Alembic migrations:** do not deploy this release against live Render while it is still at revision 0025 without explicit authorization.
- **Not cut over:** Render data has likely changed since the Oct 17 static archive; final freeze, fresh backup, independent protected copy, full row-level aggregate reconciliation, isolated backend runtime smoke, signing keys, Meta/payment webhook buffering and explicit Owner GO are pending. The Neon role password was rotated; copied prior URL is stale.

### CI acceptance — PR #47 at 8762c37b (2026-10-17)

GitHub Actions run `39017203961` confirmed **4/4 PASS** on selective release head `8762c37b6a41056b60123a63424901ba8a38199c`: `postgres-smoke`, `postgres18-neon-compatibility`, `docker-build`, and `test` (pytest). PR #47 remains **DRAFT / NOT MERGED**; CI PASS is not real-backend-to-Neon E2E and is not authorization for Production deployment. Live Render database remains the source of truth; fresh write-freeze/final backup/parity and protected cutover still pending.

## 2026-10-17 — Test-only production API cutover to Vercel + Neon VERIFIED

**Owner GO:** All existing records and provider activity are experimental; owner approved the Oct-17 Render dump as source of truth, accepting loss of any later Render test writes.

**WEB/API SWITCH PASS:** Production `directpilot.ir` frontend redeployed at **same main SHA `8592c6e9`**, Vercel deployment `dpl_AKFqXWre8HxCHVvvNz9yZeviGLF9` READY; Production-only `DIRECTPILOT_API_UPSTREAM=https://directpilot-prod-api.vercel.app`. New separate Vercel API `directpilot-prod-api` deployment `dpl_5wSJ1veseCg7BprMsGfQ4HTQ6sAJ` READY, Backend release SHA `65a3ef94`, Neon Production `directpilot_live` **83 tables / Alembic 0027**. GitHub [API ready/live/version smoke #39018969331](https://github.com/namach2727-coder/Sales-Agent/actions/runs/39018969331) PASS; [website→API plans/auth smoke #39019279518](https://github.com/namach2727-coder/Sales-Agent/actions/runs/39019279518) PASS, plan endpoint 200 and unauthenticated /auth/me 401. UAT untouched.

**Important:** The new API uses new Vercel secrets because Render secret values were inaccessible. Existing test sessions and encrypted Instagram connections may need re-login/reconnect. Meta outbound/publishing disabled, AI/payment provider secrets not migrated or end-to-end tested. Render services/DB still retained, **not deleted**. Backend draft PR #47 not yet merged; Vercel Production API project lacks automatic Git connection. Encrypted offsite backup and real browser functional acceptance remain open. Operational evidence, rollback, owner-approved test-data loss in `docs/runbooks/production_vercel_neon_cutover_20261017.md`. **Do NOT declare full feature GO-live or delete Render**.

## 2026-10-17 — Final Git source promotion for Vercel-Neon cutover

PR **#47 MERGED** to `backend-main` at `df4da87a883c590fb649d8a9f5aff2f80de5fa28` after all latest CI checks passed, including PostgreSQL 18, full test, Docker build and PostgreSQL smoke. Previous Draft/PENDING statements about PR #47 are historical and superseded. Vercel Production API deployment `dpl_5wSJ1veseCg7BprMsGfQ4HTQ6sAJ` remains READY on functionally equivalent earlier release SHA `65a3ef94`; newer release commits only added safe workflow files and docs. Vercel frontend `dpl_AKFqXWre8HxCHVvvNz9yZeviGLF9` READY using original main SHA `8592c6e9`, aliases `directpilot.ir` and `www.directpilot.ir` assigned. Test [#39019279518](https://github.com/namach2727-coder/Sales-Agent/actions/runs/39019279518) PASS confirms website API proxy and unauthenticated /auth/me protections. Neon `directpilot_live` confirmed revision `0027_traceable_receipt_versions`. Render Backend `directpilot-api` still has `autoDeploy=no`; no new Render deployment was triggered by the merge. Render service and DB are retained but no longer on Production website's API routing path. Full Meta/AI/payment gateway integration still pending due to untransferred protected Render secrets; no blanket functional acceptance. Canonical cutover runbook: `docs/runbooks/production_vercel_neon_cutover_20261017.md`.

## 2026-10-17 — Super Admin Production UI acceptance

- **User-reported PASS (manual browser acceptance):** Test customer login works on `https://directpilot.ir`. Super Admin login also works after correcting login identity; user confirmed `/admin` and **dashboard, customer list, subscriptions and payments** display correctly. This is explicit owner manual acceptance of read-only administrative navigation, **not** payment workflow / Meta / AI / production payment approval acceptance.
- **Read-only Neon staging/live DB payment preflight:** `directpilot_live` has **1 active/default payment card**, **1 manual payment** with DB-backed receipt bytes and **1 version-history row**, **25 subscription orders**, **24 tenant subscription records**, **1 active Super Admin role** (aggregate counts only; no PII or card data exposed). These counts demonstrate existing structure and records, not successful new payment operations.
- **Next controlled functional tests:** Customer chooses plan -> card number/copy -> uploads test JPEG/PNG/PDF receipt -> admin preview -> admin approval -> customer subscription reflects intended plan. Verify idempotency, failed/rejected resubmission and receipt version history. Do not use actual bank transfer. Owner's next step is to test this flow in Production's test-only environment. No database state changes performed in this checkpoint.

## 2026-10-17 — Receipt upload and admin view PASS

Owner verified that an experimental customer uploaded a receipt and the administrator received and viewed it successfully on the Production site. Independent Neon read-only checks confirm the new manual payment is approved, its associated order is paid, its subscription is active, and its stored receipt matches the version-history copy. Customer subscription UI after approval remains to be visually confirmed. Details are in docs/releases/RELEASE_REGISTER.md.

## 2026-10-17 — Production manual card-transfer subscription lifecycle accepted

**Owner final manual acceptance: PASS.** The user confirmed that, following the successfully tested experimental customer's order, manual receipt upload, Super Admin receipt viewing and payment approval, the customer portal displays the purchased plan as **active** with the **correct expiration date**. This closes the previously OPEN customer subscription UI acceptance criterion. Independent earlier read-only Neon checks established the matching `approved` manual payment, `paid` subscription order, `active` linked subscription and valid future `current_period_end`, plus intact receipt bytes and version history.

**Scope of PASS:** the normal end-to-end test-only card-to-card purchase and subscription activation path, including customer subscription display. The user performed the browser interactions and gave acceptance; the assistant performed read-only database checks. No real money transfer or assistant-initiated payment approval. Not included: rejected receipt -> resubmission and version 2, concurrency/idempotency edge cases, actual bank settlement, third-party payment gateways, Meta DM/Story/Comment automations, AI request billing, independent backup/restore, or deletion of Render.

**Release Register:** Record as final **Production (experimental) card-transfer E2E = PASS / OWNER ACCEPTED**; keep unrelated providers and exceptional cases as NOT TESTED. Current deploy topology stays Vercel frontend/backend -> Neon `directpilot_live`.
