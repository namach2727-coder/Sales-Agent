# DirectPilot — Decisions (Current)

**وضعیت as-of:** 2026-10-15. **مرجع حقیقت:** [Release Register](docs/releases/RELEASE_REGISTER.md). **منبع شواهد تاریخی بدون حذف:** [Archive Manifest](docs/runbooks/history/20261015_pre_release_register/README.md). برای تصمیم‌های انتشار، همیشه نتیجه GitHub، Vercel Alias، Neon و Render را دوباره بررسی کن.

## تصمیم‌های قطعی Owner

| ID | تصمیم | وضعیت / سند شاهد |
|---|---|---|
| D-001 | **یک Release Register** شامل شماره PR، شرح، UAT، Production، کیفیت شواهد و تأیید کاربر؛ Release بدون آن قابل ردیابی نیست | **APPROVED FOR DOCUMENTATION** در ۱۵ اکتبر؛ `docs/releases/RELEASE_REGISTER.md` |
| D-002 | **دامنه رسمی پذیرش UAT** فقط `https://uat.directpilot.ir`، Frontend Branch `UAT`، Backend مستقل Vercel + Neon مستقل | **ACCEPTED**؛ Previewهای موقت مرجع پذیرش نیستند |
| D-003 | **ذخیره تصاویر و رسیدها در PostgreSQL BYTEA**، نه R2/S3؛ هر نسخه رسید با مشتری/سفارش/پرداخت و SHA، بدون حذف پس از رد/آپلود مجدد | **ACCEPTED**؛ B#33 مسیر R2 بسته، B#34/#36 روی UAT. SLA Backup مستقل PENDING |
| D-004 | **حداقل چهار ماه بازیابی و جست‌وجوی رسید مشتری** با تاریخچه اقدامات ادمین؛ پیشنهاد پایه عملیاتی ۱۲ ماه با رعایت نگهداری قانونی/امنیتی | **PRODUCT REQUIREMENT ACCEPTED**؛ تست بازیابی بلندمدت و سیاست retention هنوز PENDING |
| D-005 | **قیمت و مدت پلن از داده واقعی Backend**؛ فقط `is_purchasable` و `trial_eligible` قواعد انتخاب را مشخص می‌کنند | **ACCEPTED**؛ Neon UAT فقط `AUTOMATION_V1` و `AI_ASSISTANT_V1` خریدنی و فقط دو Trial تخصصی ۳روزه واجدشرایط هستند |
| D-006 | **خرید چندماهه ۱..۱۲** فقط برای پلن پولی ۳۰روزه با snapshot مبلغ/مدت؛ انتقال بانکی کارت‌به‌کارت خارج از سامانه و تأیید صرفاً ادمین مجاز | **ACCEPTED WORKFLOW**؛ E2E هر محیط جداگانه PENDING |
| D-007 | انتخاب هم‌زمان DM/Story/Comment در UI = **هر کانال یک Rule مجزا** و یک واحد ظرفیت، ثبت ترتیبی؛ نام یک «Rule مشترک اتمیک» نادرست است | **ACCEPTED DOCUMENTATION**؛ UAT F#12، Production هنوز ندارد؛ Meta E2E باز |
| D-008 | منو و فرم موبایل باید دکمه مستقل Back/Close، Escape/Outside Tap و بازگشت امن داشته باشند | **ACCEPTED DOCUMENTATION**؛ UAT F#32، تست دستگاه واقعی PENDING |
| D-009 | وضعیت کد، CI، Deployment، Browser PASS، Business Signoff و Production GO **هرگز معادل یکدیگر نیستند** | **MANDATORY**؛ هر Release پنج مرحله و تأیید مستقل |
| D-010 | **تاریخچه حذف نشود**: قبل از خلاصه‌سازی پنج فایل، متن کامل byte-equivalent با Git blob SHA در Runbook archive حفظ شود | **COMPLETED AND VERIFIED**؛ `docs/runbooks/history/20261015_pre_release_register/README.md` |
| D-011 | Release واقعی Production نیازمند UAT signoff، backup، freeze/replay، data parity، rollback، ارزیابی میزبانی تجاری و GO مستقل Owner است | **HARD STOP**؛ بدون این موارد هیچ تغییر Production مجاز نیست |

## تصمیم اجرایی جدید — پذیرش P0-HEALTH-01

**P0-HEALTH-01 — UAT Health & Integration Audit:** مطابق اعلام صریح Owner در ۲۰۲۶-۱۰-۱۵ **ACCEPTED / CLOSED BY OWNER** است و نباید دوباره به‌عنوان کار باز یا پیش‌نیاز تکراری مطرح شود. دامنه تأیید: بررسی اتصال Frontend/Backend/Neon، سلامت ثبت‌نام/ورود/خروج/Session، دریافت پلن/Trial و خطاهای حیاتی UAT طبق چک‌لیست P0-01 مکالمه. این تأیید کاربر جایگزین شواهد ثبت‌نشده CI، تست مستقل یا تأیید E2E خرید، Meta و Production نیست. فقط در صورت Regression جدید با شواهد مشخص بازگشایی شود.

این پذیرش مجوز Production GO یا بستن سایر موارد P0 نیست.

## تصمیم‌های باز؛ نباید قطعی تفسیر شوند

- قیمت‌های Production Render و تفاوت با کاتالوگ Neon UAT: **UNVERIFIED**، جدول UAT مجوز تغییر Production نیست.
- ساختار Atomic batch یا گروه‌بندی ظاهری Ruleهای سه‌کاناله، موتور Meta و انتشار واقعی: **NOT DECIDED / E2E PENDING**.
- SLA عملیاتی ۱۲ماهه و Backup off-provider با Restore دوره‌ای: **PENDING**.
- نوع پلن تجاری Vercel/میزبان نهایی Production و زمان cutover: **PENDING**.

**جزئیات تاریخی و چرایی تصمیم‌ها** دست‌نخورده در Runbookهای پیشین، Archive و Git باقی مانده‌اند؛ این سند جای تاریخچه طولانی نیست.

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
