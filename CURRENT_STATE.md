# DirectPilot — Current State (Verified Snapshot)

**وضعیت as-of:** 2026-10-15. **مرجع حقیقت:** [Release Register](docs/releases/RELEASE_REGISTER.md). **منبع شواهد تاریخی بدون حذف:** [Archive Manifest](docs/runbooks/history/20261015_pre_release_register/README.md). برای تصمیم‌های انتشار، همیشه نتیجه GitHub، Vercel Alias، Neon و Render را دوباره بررسی کن.

## وضعیت محیط‌ها و شواهد (۱۵ اکتبر)

| محیط | نسخه/آدرس | نتیجه |
|---|---|---|
| Frontend UAT | `uat.directpilot.ir`, Git `UAT`, `dad3a3790246f96fbbe760d26e2415afd0a45851`; Vercel `dpl_GGgg4EkaQF3bExfnzbfgRBK1GLhj` | **READY / Git CI PASS**؛ تست موبایل واقعی هنوز PENDING |
| Backend UAT | `directpilot-uat-api.vercel.app`, Git `migration/vercel-uat-fastapi-20261014`; Neon `round-shape-42044596/neondb` | **/ready PASS**؛ Migration `0027_traceable_receipt_versions` |
| Data UAT | Receipt latest=۲، receipt version-1=۲، تطبیق بایت/رابطه=۲/۲، product image=۰ | **Backfill PASS**؛ آپلود/بازیابی واقعی و چهارماه SLA PENDING |
| Frontend Production | `directpilot.ir`, Git `main`, `8592c6e91d4beaed7c31653dc285612fd511fa53`, Vercel `dpl_cRZsk7rndqFWH1KnKdhLVbNU1VxF` | **READY**؛ source code محتوای مشخص را ثابت می‌کند نه تست پرداخت کامل |
| Backend/DB Production | Render همچنان مرجع | **NO CUTOVER**؛ کاتالوگ و DB Production از این بررسی قابل اثبات کامل نیستند |

## پذیرش اخیر و وضعیت ممیزی سلامت

**P0-HEALTH-01 — UAT Health & Integration Audit:** مطابق اعلام صریح Owner در ۲۰۲۶-۱۰-۱۵ **ACCEPTED / CLOSED BY OWNER** است و نباید دوباره به‌عنوان کار باز یا پیش‌نیاز تکراری مطرح شود. دامنه تأیید: بررسی اتصال Frontend/Backend/Neon، سلامت ثبت‌نام/ورود/خروج/Session، دریافت پلن/Trial و خطاهای حیاتی UAT طبق چک‌لیست P0-01 مکالمه. این تأیید کاربر جایگزین شواهد ثبت‌نشده CI، تست مستقل یا تأیید E2E خرید، Meta و Production نیست. فقط در صورت Regression جدید با شواهد مشخص بازگشایی شود.

**اولویت باز بعدی:** P0-02 (سناریوهای Auth و جریان کسب‌وکار)؛ موارد E2E پیشین همچنان باز هستند و نباید صرفاً با این تأیید PASS اعلام شوند.

## تفاوت‌های مهم UAT و Production

- **در هر دو Frontend deployed source وجود دارد:** خرید چندماهه (`ordersApi.create(id,months)`)، نمایش/کپی شماره کارت؛ همچنین PRهای گزینشی Production برای Dashboard و `/solutions` ثبت شده‌اند. این‌ها را مجدداً به‌عنوان قابلیت منتظر انتشار فهرست نکنید؛ E2E مالی همچنان باز است.
- **در UAT و نه Production deployed source:** انتخاب ۱/۲/۳ DM/Story/Comment F#12، آرشیو رسیدهای نسخه‌دار و جست‌وجو F#31/B#36، محصول BYTEA B#34، اصلاح non-blocking Login F#31 و ناوبری Back/Close جدید F#32.
- **انتشارهای محتوایی/SEO/GA4:** Frontend Production PRهای F#1–#9، F#27، F#29، F#30 را دارد؛ صحت ردیابی Realtime، Indexing و رفتار موبایل مستقل از Merge است.
- **کاتالوگ Neon UAT:** ۸ ردیف؛ خرید مجاز فقط `AUTOMATION_V1` و `AI_ASSISTANT_V1`، Trial واجدشرایط فقط `AUTOMATION_TRIAL`, `AI_ASSISTANT_TRIAL` و ۳روزه. `START/PRO` فعال ولی غیرقابل‌خرید، `TRIAL` قدیمی فعال اما غیرواجدشرایط، `FREE` غیرفعال. جدول قیمت/سقف‌ها در Release Register.

## شواهد اجرایی و موارد باز

- UAT mobile PR F#32: ۲۲۳ تست، TypeScript، ESLint، Next Build **PASS**. UAT API routing/domain smoke PASS. Vercel SSO ممکن است صفحات HTML را برای بازدیدکننده بدون مجوز محافظت کند.
- **OPEN:** مرورگر واقعی مشتری/ادمین، Back/Close آیفون و اندروید، UX و سرعت، Meta سه کاناله end-to-end، جریان پرداخت ساختگی/نسخه رسید، تصویر محصول، Backup مستقل، GA4/SEO KPI و ردیف‌های نامشخص Production.
- **هیچ تغییر Production** در عملیات «Release Register و خلاصه‌سازی مستندات» اعمال نشده است. تأیید Owner فقط شش مورد اصلاح مستنداتی را پوشش می‌دهد.

برای هر قابلیت و PR از [Release Register](docs/releases/RELEASE_REGISTER.md) و Runbookهای پذیرش استفاده کنید. تاریخچه خام و توضیحات مراحل قبل در Archive محفوظ است.

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

## Backend readiness — PR #47 (2026-10-17)

Selective backend and schema 0027 changes are prepared in Draft PR #47. CI is being checked. Neon restored candidate is independent; no live Render service or production traffic change was made. Final data parity and cutover approvals remain pending.

### CI acceptance — PR #47 at 8762c37b (2026-10-17)

GitHub Actions run `39017203961` confirmed **4/4 PASS** on selective release head `8762c37b6a41056b60123a63424901ba8a38199c`: `postgres-smoke`, `postgres18-neon-compatibility`, `docker-build`, and `test` (pytest). PR #47 remains **DRAFT / NOT MERGED**; CI PASS is not real-backend-to-Neon E2E and is not authorization for Production deployment. Live Render database remains the source of truth; fresh write-freeze/final backup/parity and protected cutover still pending.

## 2026-10-17 — Owner clarified Production usage is test-only

Owner explicitly stated **all current usage is experimental**: no real customers, payments or Instagram webhook operations that require commercial continuity. This reduces outage/replay SLA obligations but **does not authorize silent loss of experimental changes after the 2026-10-17 10:33 Render backup**. Render hosted database read-only query attempted by connector but blocked by Render external IP allowlist, so actual post-backup source delta remains unknown. Release PR #47 already has CI 4/4 PASS and remains draft; Neon directpilot_live is ready at revision 0027. Next decision: Owner approval to use the Oct-17 restored staging snapshot as test source of truth and discard any newer Render test changes, OR obtain a fresh source dump during controlled final sync. Frontend must use backend HTTP, never direct Postgres. Do not change Render live DATABASE_URL or production Vercel API routing until this decision and runtime compatibility work.

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
