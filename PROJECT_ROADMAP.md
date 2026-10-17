# DirectPilot — Project Roadmap (Current)

**وضعیت as-of:** 2026-10-15. **مرجع حقیقت:** [Release Register](docs/releases/RELEASE_REGISTER.md). **منبع شواهد تاریخی بدون حذف:** [Archive Manifest](docs/runbooks/history/20261015_pre_release_register/README.md). برای تصمیم‌های انتشار، همیشه نتیجه GitHub، Vercel Alias، Neon و Render را دوباره بررسی کن.

## North Star و محیط‌ها

هدف: SaaS قابل اعتماد با جریان ثبت‌نام تا دریافت رسید، قوانین اتوماسیون DM/Story/Comment، دستیار AI و پنل‌های قابل استفاده موبایل. **مرجع پذیرش: `uat.directpilot.ir`**؛ Backend UAT Vercel + Neon UAT مستقل. Production واقعی همچنان Render برای API/DB و Vercel `main` برای Frontend است. Release Register وضعیت جزئی و PR هر قابلیت را نگهداری می‌کند، نه این Roadmap.

## P0 — تثبیت UAT پیش از هر Cutover (OPEN)

**P0-HEALTH-01 — UAT Health & Integration Audit:** مطابق اعلام صریح Owner در ۲۰۲۶-۱۰-۱۵ **ACCEPTED / CLOSED BY OWNER** است و نباید دوباره به‌عنوان کار باز یا پیش‌نیاز تکراری مطرح شود. دامنه تأیید: بررسی اتصال Frontend/Backend/Neon، سلامت ثبت‌نام/ورود/خروج/Session، دریافت پلن/Trial و خطاهای حیاتی UAT طبق چک‌لیست P0-01 مکالمه. این تأیید کاربر جایگزین شواهد ثبت‌نشده CI، تست مستقل یا تأیید E2E خرید، Meta و Production نیست. فقط در صورت Regression جدید با شواهد مشخص بازگشایی شود.

**توضیح شناسه:** P0-01 جدول زیر مربوط به «ثبت انتشار و مستندات» است و پیش‌تر DONE بوده؛ شناسه ممیزی سلامتِ پذیرفته‌شده در گفت‌وگو `P0-HEALTH-01` است. هر دو بسته‌اند و نباید دوباره در صف اجرا قرار گیرند.

| شناسه | خروجی / معیار خروج | وضعیت و مالک پذیرش |
|---|---|---|
| P0-01 | ثبت انتشار با PR، محیط، SHA، UAT/Production و Owner Acceptance | **DONE — مستندسازی تأییدشده، پذیرش قابلیت‌ها جداست** |
| P0-02 | گردش کامل ثبت‌نام، طرح قابل‌خرید، Trial واقعی و سفارش ۱..۱۲ ماه | **CODE DEPLOYED؛ تست مشتری/Backend و سیاست قیمت PENDING** |
| P0-03 | کارت‌به‌کارت، کپی، رسید ساختگی، تأیید/رد ادمین، اثر روی Entitlement و Audit | **CODE DEPLOYED؛ end-to-end PENDING** |
| P0-04 | بازیابی نسخه‌های قبلی رسید، SHA/tenant RBAC، جست‌وجوی تاریخ و بازیابی ۴ ماه | **Neon UAT 0027/بک‌فیل ۲/۲ PASS؛ E2E و Backup مستقل PENDING** |
| P0-05 | تصاویر محصول در BYTEA: آپلود→preview→redeploy→حذف | **Migration/CI PASS؛ Browser E2E PENDING** |
| P0-06 | سه‌کاناله DM/Story/Comment: یک تا سه Rule، سهمیه، شکست میانی، Meta E2E | **UI/CI UAT PASS؛ Meta live E2E BLOCKED/PENDING** |
| P0-07 | ناوبری موبایل/ادمین/مشتری در 320/360/375/390/768px + دسترس‌پذیری | **F#32 و CI ۲۲۳ PASS؛ بررسی دستگاه واقعی PENDING** |
| P0-08 | UAT مرورگر با Vercel SSO، نقش‌ها، Login/Logout و تاخیر سرد `auth/me` | **HTTP smoke PASS؛ real-browser/performance PENDING** |
| P0-09 | SEO/GA4 `page_view`, `signup_intent`, `sign_up`: رویدادهای واقعی و Noindex UAT | **PRهای Production قبلی؛ اندازه‌گیری PENDING** |

جزئیات و دستور تست: `docs/runbooks/uat_customer_billing_acceptance_20261015.md` و `docs/runbooks/uat_multichannel_mobile_acceptance_20261015.md`. هر PASS واقعی باید در Release Register با تاریخ، دستگاه و شواهد ثبت گردد.

## P1 — بازطراحی UX هدفمند پس از تست واقعی (OPEN)

1. پس از ثبت Pain Point واقعی، بهینه‌سازی سلسله‌مراتب Dashboard مشتری، بخش Subscription/Billing، پنل ادمین پرداخت و فرم‌های بلند اتوماسیون؛ داده مشتری و CTAها نباید گم شوند.
2. Performance budget موبایل: cold-start `/auth/me`، TTFB، TTI، واکنش منو و کیفیت شبکه موبایل؛ تمرکز صرف بر زیبایی بدون اندازه‌گیری ممنوع.
3. بررسی محتوای پلن، محدودیت‌های AI/Automation، متن سه‌روز Trial مطابق `saas_plans` و عدم بازگشت پیام «۱۴ روز» یا «Free forever» برای ردیف‌های legacy.

## P2 — Production cutover (BLOCKED; approval separate)

1. بررسی قانونی/هزینه‌ای میزبان Production؛ محدودیت استفاده تجاری پلن Hobby Vercel مانع بالقوه است.
2. Backup کامل مستقل و قابل بازیابی از Render Production DB + آزمایش Restore؛ عدم استفاده از کپی قدیمی Neon به‌عنوان داده نهایی.
3. Inventory تمام writers, schedulerها، Media و Webhookهای Meta و پرداخت و Buffer/Replay با dedup؛ Freeze کنترل‌شده و جلوگیری از split-brain.
4. Sync کامل و نهایی Production به Neon Production `directpilot_live`، Alembic موردنیاز، تطبیق جدول/فاکتور/اشتراک/پرداخت/خروجی/تعداد/مبالغ و مجوزهای امنیتی.
5. Dry run و برنامه Rollback تست‌شده، معیار توقف و نظارت؛ **GO جداگانه Owner** پیش از جابه‌جایی Domain، DNS، callback یا خاموش‌کردن Render.

**هیچ اشتباه تکراری:** Merge کردن کل Branch `UAT` به `main` ممنوع؛ انتشار Prod باید PRهای منتخب، شواهد ردیف مربوط و تأیید مجزای Owner داشته باشد.

## P3 — شواهد و نگهداری (ONGOING)

- ثبت Release Register به ازای هر PR و Deployment؛ پنج فایل فقط summary باشند.
- شواهد تاریخی پنج سند (حدود نیم‌میلیون نویسه) دقیقاً و بدون تغییر در `docs/runbooks/history/20261015_pre_release_register/` بایگانی شده‌اند؛ حذف یا دستکاری آن ممنوع است.
- حفظ تصمیم PostgreSQL BYTEA (نه R2/S3)، ۴+ ماه Traceability رسیدها و UI موبایل دارای Back/Close.

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

## 2026-10-17 — Production manual payment receipt acceptance (verified)

- **User browser evidence:** Experimental customer successfully uploaded a receipt through `directpilot.ir`, and Super Admin received and opened it in the admin payment view. Customer upload + admin receipt visibility: **PASS (owner confirmed)**.
- **Independent read-only Neon evidence, `directpilot_live`:** Latest manual-card-transfer payment created 2026-10-17 10:05:29Z; receipt submitted 10:05:50Z and payment marked `approved` at 10:06:26Z; order `paid`; one linked subscription `active` with a valid future period end. Current aggregate: 2 manual payments, both with inline receipt bytes, 2 receipt-version records. Latest receipt: 67,073 bytes; current bytes equal the version-1 archive bytes; recorded SHA-256 and byte sizes agree. **Status of DB payment approval + subscription activation: PASS (database evidence)**. No payment was created or approved by the assistant.
- **Limits:** Browser display of the active customer subscription after approval is *not yet owner-confirmed*; customer card-copy button, rejected receipt resubmission/version 2, Meta/AI/provider payment integrations, backup resilience are *not verified*. No real bank transfer required. Never log receipt contents, card values, user emails or tokens in the release notes.

## 2026-10-17 — Production manual card-transfer subscription lifecycle accepted

**Owner final manual acceptance: PASS.** The user confirmed that, following the successfully tested experimental customer's order, manual receipt upload, Super Admin receipt viewing and payment approval, the customer portal displays the purchased plan as **active** with the **correct expiration date**. This closes the previously OPEN customer subscription UI acceptance criterion. Independent earlier read-only Neon checks established the matching `approved` manual payment, `paid` subscription order, `active` linked subscription and valid future `current_period_end`, plus intact receipt bytes and version history.

**Scope of PASS:** the normal end-to-end test-only card-to-card purchase and subscription activation path, including customer subscription display. The user performed the browser interactions and gave acceptance; the assistant performed read-only database checks. No real money transfer or assistant-initiated payment approval. Not included: rejected receipt -> resubmission and version 2, concurrency/idempotency edge cases, actual bank settlement, third-party payment gateways, Meta DM/Story/Comment automations, AI request billing, independent backup/restore, or deletion of Render.

**Release Register:** Record as final **Production (experimental) card-transfer E2E = PASS / OWNER ACCEPTED**; keep unrelated providers and exceptional cases as NOT TESTED. Current deploy topology stays Vercel frontend/backend -> Neon `directpilot_live`.

## 2026-10-17 — Infrastructure vs integrations audit (Render retirement blocked)

**Audit after user asked whether Render dependencies and all environment variables were migrated: Answer NO.** Production public web → Vercel `directpilot-prod-api` → Neon `directpilot_live` is tested and working for customer/admin login and manual card-transfer workflow. This does NOT mean all provider integrations and secrets were migrated.

**Connected Vercel inspection (configuration names only, not secret values):** Backend project `directpilot-prod-api` currently has **14 environment keys**, including `DATABASE_URL`, `APP_ENV`, `APPLICATION_SECRET`, `INSTAGRAM_TOKEN_ENCRYPTION_KEY`, `TRUSTED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `FORCE_HTTPS`, `SESSION_COOKIE_SECURE`, `LEGACY_ADMIN_ADAPTER_ENABLED`, `DEBUG`, `DATABASE_POOL_SIZE`, `DATABASE_MAX_OVERFLOW`, `META_SEND_ENABLED`, `META_CONTENT_PUBLISH_ENABLED`. It does **not** show `META_APP_ID`, `META_APP_SECRET`, `META_VERIFY_TOKEN`, `META_OAUTH_REDIRECT_URI`, `OPENAI_API_KEY`, `GROQ_API_KEY`, `KPAY_ACCESS_TOKEN`, or `PAYEXA_API_KEY`. Outbound Meta send/publish was configured OFF for cutover. A Fernet encryption key *exists*, but it was newly provisioned rather than copied from inaccessible Render secret; it may not decrypt historical tokens.

**Neon read-only Meta inventory:** 1 Instagram connection row with database status `active` and an encrypted access token, 18 historical webhook delivery rows and 7 inbound events; latest recorded webhook at 2026-10-11 07:28:59Z. Database status `active` is NOT validation of current OAuth token decryptability, Meta webhook routing or working DM/Story/Comment automation.

**Render inventory:** Both `directpilot-api` and `directpilot-uat-api` remain provisioned and not suspended, autoDeploy=off. Frontend Production API proxy no longer uses Render for its normal requests, but Meta OAuth/webhook callback addresses and third-party callbacks have not been independently verified, so **zero external Render dependency is NOT established**.

**Exit gate before Render retirement:** Retrieve original Render secret values through an owner-controlled secure channel where technically possible (never in chat/repo); restore valid Meta app/verify/webhook/OAuth configuration and confirm developer-dashboard callback URLs target Vercel; handle old Fernet-encrypted tokens by restoring the original encryption key or reconnecting Instagram; configure/test AI/payment-provider secrets where needed; test DM, Story, Comment, callbacks, media uploads, retries and UAT; confirm backups. Only then consider a separately approved shutdown/deletion of Render resources. Do not write invented API keys or say migration is complete.

## 2026-10-17 — Meta Production environment-variable inventory (user completed)

Owner confirmed they created the Meta variables on Vercel. Connector-verified `directpilot-prod-api` environment now has **27 keys**, up from 14, including these 13 new **Production-only** Meta keys: `META_VERIFY_TOKEN`, `META_SIGNATURE_REQUIRED`, `META_SEND_ALLOWED_ACCOUNT_IDS`, `META_RELAY_TIMEOUT_SECONDS`, `META_OAUTH_TOKEN_URL`, `META_OAUTH_TIMEOUT_SECONDS`, `META_OAUTH_STATE_TTL_MINUTES`, `META_OAUTH_STATE_PREFIX`, `META_OAUTH_REDIRECT_URI`, `META_OAUTH_AUTHORIZE_URL`, `META_GRAPH_BASE_URL`, `META_APP_SECRET`, `META_APP_ID`. Existing `META_SEND_ENABLED` and `META_CONTENT_PUBLISH_ENABLED` remain configured OFF, and existing `INSTAGRAM_TOKEN_ENCRYPTION_KEY` was created during cutover (NOT confirmed to match historical Render Fernet key). **Sensitive values are not exposed by the connector and were not validated; configuration presence does not prove validity, Meta callback registration, token decryptability or integration readiness.** Production OAuth callback path in Backend: `/api/v1/integrations/instagram/callback`; webhook path: `/api/v1/integrations/instagram/webhook`. Meta relay target keys shown blank in owner screenshot; leave blank for Production per validation policy. Next critical prerequisite is replacing existing Vercel `INSTAGRAM_TOKEN_ENCRYPTION_KEY` with the same old Production Render value (owner copies directly in provider consoles, never chat), **OR** arranging Instagram account reauthorization if original key cannot be recovered. Then verify authorized Meta developer OAuth redirect/Webhook URLs and redeploy and smoke-test before enabling outbound sends. `META_API_VERSION` optional Vercel variable not present, code default `v24.0`. Render deletion remains blocked.

## 2026-10-17 — Instagram Fernet key transfer, OAuth correction and security smoke

**Owner action and Vercel confirmation:** Owner states the original `INSTAGRAM_TOKEN_ENCRYPTION_KEY` was copied directly from old Render Production to Vercel `directpilot-prod-api` without sharing its value. Vercel metadata confirms this sensitive variable was updated at 2026-10-17 (Unix milliseconds 1792233378759). This confirms a change, **NOT cryptographic equality or ability to decrypt historical Instagram tokens**. No secret exposed in GitHub or chat.

**Production configuration:** `META_OAUTH_REDIRECT_URI` in Vercel Production was set to **`https://directpilot-prod-api.vercel.app/api/v1/integrations/instagram/callback`**. Vercel Production `META_SEND_ENABLED=false` and `META_CONTENT_PUBLISH_ENABLED=false` remain unchanged. Other 13 Meta keys previously entered by owner present but sensitive values unverifiable.

**Release:** Independent Vercel Production API deployed from known/merged Backend SHA `df4da87a883c590fb649d8a9f5aff2f80de5fa28`, deployment **`dpl_4jxhit3evN5CCUwYDAJV7aEgZ9Ct` READY** and alias `directpilot-prod-api.vercel.app` assigned. After deploy, GitHub Actions [Neon API health smoke](https://github.com/namach2727-coder/Sales-Agent/actions/runs/39018969331) rerun **PASS** (GET /ready -> HTTP 200, status=ready, database=available, migration=current; /live 200, /version 200).

**Meta negative-path smoke [#39025898052](https://github.com/namach2727-coder/Sales-Agent/actions/runs/39025898052) PASS:** Meta webhook verification GET with deliberately wrong verify token -> **HTTP 403**; unsigned/invalid HMAC webhook POST -> **HTTP 401**; OAuth callback without code/state -> **HTTP 422**. These checks establish endpoints accessible and security configuration loaded, **NOT** Meta Developer console callback configuration, valid OAuth, decryption of historic encrypted tokens, actual webhook deliveries, or outbound replies.

**Next owner step:** In Meta Developers for the corresponding app, allowlist OAuth redirect EXACTLY `https://directpilot-prod-api.vercel.app/api/v1/integrations/instagram/callback`; update Webhooks Callback URL EXACTLY `https://directpilot-prod-api.vercel.app/api/v1/integrations/instagram/webhook` and use the unchanged same `META_VERIFY_TOKEN` value in Meta UI (do not paste into chat). Save/verify and test one isolated Instagram reauthorization and webhook. Do not flip Meta sending/publishing to true or decommission Render yet. No real Meta send initiated.

## 2026-10-17 — Meta Graph code 101 is not proof of invalid Instagram Login credentials

Owner ran read-only PowerShell Meta diagnostic. A no-token `GET https://graph.facebook.com/v24.0/me` returned HTTP 400 (normal, Graph reachable), whereas Facebook Graph app-token issuance `POST https://graph.facebook.com/v24.0/oauth/access_token` with locally entered credentials returned HTTP 400, Graph `OAuthException` code **101** (commonly invalid Facebook application ID). **Critical correction:** DirectPilot backend `app/instagram_onboarding/provider.py` explicitly uses **Instagram API with Instagram Login**, with `https://www.instagram.com/oauth/authorize` and `https://api.instagram.com/oauth/access_token`; its `META_APP_ID`/`META_APP_SECRET` are the credential pair used as Instagram `client_id`/`client_secret`. Meta's **Instagram App ID/Secret** can differ from the main **Facebook Meta App ID/Secret** used by `graph.facebook.com`. Consequently the Graph 101 diagnostic **cannot validate or invalidate an Instagram App ID/Secret pair** and must not trigger unjustified credential rotation. The earlier scripts v2/v3 targeted the wrong API for this architecture unless supplied the *Facebook app* credential pair.

**Safest next step:** Ask owner which source they used for Vercel `META_APP_ID`/`META_APP_SECRET` (Instagram → API setup with Instagram Login, Meta App Settings → Basic, or Render previous production); do not ask them to transmit either value. Then check correct Instagram Login pair and the original Meta Developer registered callback. Never enable sending or disconnect Render before verified real OAuth/Webhook tests. Current status `META_FERNET_TRANSFER_OWNER_REPORTED / BACKEND_HEALTH_PASS / META_NEGATIVE_SECURITY_PASS / INSTAGRAM_OAUTH_REAL_UNVERIFIED / META_DASHBOARD_LOGIN_BLOCKED / RENDER_RETIREMENT_BLOCKED`. No Meta subscriptions, tokens, or environment settings changed in these read-only probes.

## 2026-10-17 — Telegram bot-builder future track ACTIVATED for exploration

Owner changed product priority: Instagram Meta integration PAUSED. Start **independent product discovery/engineering**, not an expansion of Instagram Production MVP: Telegram No-Code AI Bot Builder, Manager Bot + user-approved Managed Bots + Mini App. Initial isolated branch `feature/telegram-managed-bots-spike-20261017`. See `docs/telegram_bot_builder/MVP_BLUEPRINT.md` on that branch. Phasing: T0 offline API primitives and tests; T1 isolated UAT bot manager/service and tenant-safe webhook; T2 Mini App no-code menu/FAQ/keyword/rules/publish; T3 AI, lead forms, human handoff and analytics; later flow builder/payments/CRM. No rollout or real token until separately reviewed. DirectPilot Production untouched.

## 2026-10-17 — Product name and database boundary for DirectPilot TelBot

**Owner-confirmed product name:** **DirectPilot TelBot** (دایرکت‌پایلوت تل‌بات); this is the separate Telegram no-code bot-builder product, not the existing Instagram DirectPilot service. **Current database status:** NOT CREATED (prototype is offline-only). **Target architecture, proposal not yet provisioned:** distinct Neon PostgreSQL project (suggested label `directpilot-telbot`) with dedicated **UAT and Production logical isolation** (separate databases/branches with no shared customer data or secrets); distinct Vercel TelBot API and Telegram Mini App projects. Do not use the existing DirectPilot Production Neon `directpilot_live` database or reuse its tokens/encryption keys. Encrypted child bot credentials, tenant scoping, webhook idempotency, Mini App initData verification, backup policy and least-privilege must be implemented before user onboarding. Naming was provided by owner; no Neon/Vercel infrastructure is created or changed by this documentation step. Meta migration remains PAUSED.

## 2026-10-17 — DirectPilot TelBot Neon provisioned and verified

**LIVE INFRA (owner approved "بسازیم"; this supersedes prior NOT CREATED plan):** Created independent Neon project `directpilot-telbot` in owner org `org-dawn-firefly-87600084` on **Free** plan; project ID `curly-cell-93038441`, region `aws-us-west-2`, PostgreSQL **18.6**, primary branch `production` ID `br-fancy-feather-arydwgj7`, UAT branch `uat` ID `br-tiny-poetry-arz49v2o` (child of empty production). **Both branches contain a database named `telbot`**, isolated at Neon branch level, with database role `telbot_owner`. **Read-only SQL on each branch confirmed database `telbot`, correct PostgreSQL version and `0` public tables.** Owner link: https://console.neon.tech/app/projects/curly-cell-93038441 . The UAT branch is the ONLY intended development database; no Telegram schema, tenant, token, migration, data or bot activity was created. Mainline DirectPilot/Instagram Neon project `billowing-poetry-05589994` and its Production DB `directpilot_live` remain unchanged. Vercel TelBot API/Mini App not provisioned. No connection string, password or API key copied to chat or committed to repository.

**Guardrails:** Branches are not marked protected (Neon Free account); do not assume isolated database credentials just from separate branch names. Before deploying UAT generate/rotate dedicated branch credentials and configure scoped Vercel UAT environment securely; never commit URLs/passwords. Set up backups and a migration framework before creating commercial customer data. Cost: Neon Free plan confirmed by organization inspection; project compute resource defaults are managed by Neon. Meta migration remains paused.

## 2026-10-17 — DirectPilot TelBot T1 database foundation deployed to Neon UAT

**Authorized implementation result:** Versioned additive migration `0001_telbot_foundation` committed in isolated GitHub branch `feature/telegram-managed-bots-spike-20261017`, path `experiments/telegram_bot_builder/migrations/0001_telbot_foundation.sql`, source commit `899a5df77c826056b291f64ae09f677d18dd8d34`. Executed as a **single atomic Neon SQL transaction only on UAT**: project `curly-cell-93038441`, branch `br-tiny-poetry-arz49v2o`, PostgreSQL DB `telbot`. **UAT deployment/SQL verification PASS:** schema `telbot`, 13 tables, 18 foreign-key constraints, 39 check constraints, 33 indexes, migration version record `0001_telbot_foundation`. Zero records in all 12 functional/business tables; migration ledger has 1 record. Database content covers tenant/user roles, Managed Bot creation request, bot ownership and encrypted-token ciphertext slots, publishable config versions, menu buttons, keyword rules, FAQs, chat sessions, idempotent inbound updates, outbound deliveries and tenant-scoped audit events. Composite tenant FKs block ordinary cross-tenant FK associations; this is schema-level segregation, NOT yet verified RLS or API authz.

**Database live integrity smoke:** rollback-only SQL `experiments/telegram_bot_builder/migrations/0001_telbot_uat_smoke_rollback.sql` executed on UAT and PASS; expected constraint rejects for duplicate `(bot_id,telegram_update_id)`, second published configuration, mismatched tenant references, cross-tenant owner and active bot without encrypted credential. The intentional rollback restored UAT to empty business tables. Offline branch CI [workflow 39035278379](https://github.com/namach2727-coder/Sales-Agent/actions/runs/39035278379) **13/13 tests PASS** (8 original primitives + 5 schema-contract checks). No real Telegram API/network calls.

**Production untouched:** TelBot production branch `br-fancy-feather-arydwgj7` remains **0 tables**; DirectPilot Instagram Production DB `directpilot_live`, Vercel apps and Render services were not modified. No TelBot API deployment, live Telegram bot, webhook, Mini App, vault encryption implementation, RLS/role separation or data migrations to Production exist yet. Next implementation gate: develop isolated TelBot UAT backend API and service-layer tenant authorization with dedicated, non-owner application DB role/credentials, webhook idempotency workflow, and safe token encryption; no Production deploy without owner acceptance. Do not paste real DB connection URLs/Telegram tokens in GitHub or chat.

## 2026-10-17 — TelBot T1 API and security foundation (UAT only)

**Scope:** Owner approved "رو گام بعدی" for DirectPilot TelBot UAT backend development, not deployment into TelBot or Instagram Production. Source isolated in `feature/telegram-managed-bots-spike-20261017`, `experiments/telegram_bot_builder/`.

**Implemented on branch:** `auth.py` official Telegram Mini App `initData` HMAC verification, signature/freshness/duplicate rejection; `vault.py` Fernet encryption/decryption with a dedicated TelBot key (currently isolated cryptographic component, NOT yet wired to actual child-bot token retrieval/persistence); `api.py` independent FastAPI /live, /ready, tenant-scoped read bots/config, authorized create draft/publish, authenticated Manager Bot and child-bot webhook idempotent receipt. Webhooks persist update metadata but do NOT send Telegram messages; Manager Bot onboarding, secure token retrieval `getManagedBotToken`, actual provider registration, public Mini App interface and AI remain NOT implemented. UAT API packaging `api/index.py`, `vercel.json`, `requirements.txt` and `DEPLOYMENT.md` prepared.

**Neon UAT DB:** additive migration `0002_webhook_auth` applied atomically ONLY on `curly-cell-93038441` branch `br-tiny-poetry-arz49v2o`, DB `telbot`: new `bots.webhook_secret_digest` and `manager_inbound_updates`. SQL verified **14 UAT tables**, versions `0001_telbot_foundation, 0002_webhook_auth`, zero tenant records. **TelBot Production `br-fancy-feather-arydwgj7` remains zero tables.**

**Security role:** Initial Neon API-created role `telbot_uat_api` was found **overprivileged** (Neon API grants neon_superuser). It was REVOKED and DELETED. Replaced with SQL-created least-privilege UAT role **`telbot_ua_runtime`**, NOSUPERUSER/NOCREATEDB/NOCREATEROLE/NOBYPASSRLS, SELECT/INSERT/UPDATE on telbot schema, NO DELETE, NO migration-ledger writes. Role has **NULL password**, deliberately cannot be used to connect yet. Branch UAT ready for later direct credential provisioning through safe channel, never in chat/GitHub. No live tokens, bot accounts or DB records created.

**Tests:** [Isolated TelBot API CI run 39036798043](https://github.com/namach2727-coder/Sales-Agent/actions/runs/39036798043) PASS (29 offline tests; Telegram Mini App HMAC, tenant membership, fail-closed webhook, idempotent duplicates, Fernet vault, migration contracts and initial Managed Bot primitives). Database constraints were separately smoke tested and passed; no real Telegram network call.

**Deployment blocker:** Attempt to create **separate Vercel `directpilot-telbot-uat-api` project** with connector was denied **HTTP 403 Forbidden, no project creation permission**. No Vercel deployment or env creation occurred. CLI fallback unavailable (no authenticated vercel CLI in sandbox). Owner must create project in their Vercel dashboard, or grant appropriate Vercel project-create permission; then connect the isolated UAT package. No production changes, no Meta changes (Meta integration still PAUSED). Never claim TelBot API deployed or usable with real Telegram before owner creates dedicated Manager Bot via @BotFather, adds secrets securely, and end-to-end UAT passes.
