# DirectPilot — Next Actions (Prioritized)

**وضعیت as-of:** 2026-10-15. **مرجع حقیقت:** [Release Register](docs/releases/RELEASE_REGISTER.md). **منبع شواهد تاریخی بدون حذف:** [Archive Manifest](docs/runbooks/history/20261015_pre_release_register/README.md). برای تصمیم‌های انتشار، همیشه نتیجه GitHub، Vercel Alias، Neon و Render را دوباره بررسی کن.

## بسته‌شده و خارج از صف

**P0-HEALTH-01 — UAT Health & Integration Audit:** مطابق اعلام صریح Owner در ۲۰۲۶-۱۰-۱۵ **ACCEPTED / CLOSED BY OWNER** است و نباید دوباره به‌عنوان کار باز یا پیش‌نیاز تکراری مطرح شود. دامنه تأیید: بررسی اتصال Frontend/Backend/Neon، سلامت ثبت‌نام/ورود/خروج/Session، دریافت پلن/Trial و خطاهای حیاتی UAT طبق چک‌لیست P0-01 مکالمه. این تأیید کاربر جایگزین شواهد ثبت‌نشده CI، تست مستقل یا تأیید E2E خرید، Meta و Production نیست. فقط در صورت Regression جدید با شواهد مشخص بازگشایی شود.

## P0 — پیش از امضای UAT

1. [ ] **تست مشتری در `uat.directpilot.ir`:** Register/Login، شروع Trial واجدشرایط سه‌روزه، انتخاب پلن قابل خرید، سفارش ۱..۱۲ ماه، مبلغ/مدت snapshot، نمایش/کپی شماره کارت، آپلود رسید ساختگی و Refresh/Logout. از `docs/runbooks/uat_customer_billing_acceptance_20261015.md` تبعیت کن.
2. [ ] **تست ادمین با داده ساختگی:** فقط حساب ادمین UAT؛ مشاهده/رد/آپلود مجدد نسخه ۱ و ۲، جست‌وجو با ایمیل/تاریخ، SHA و timeline، جلوگیری از دسترسی کاربر غیرمجاز. هیچ رسید واقعی تأیید نشود.
3. [ ] **تست تصاویر محصول در Neon BYTEA:** JPEG کوچک، آپلود/preview/redeploy/delete، کنترل سهمیه ۲ MiB/تصویر و ۵۰ MiB/فروشگاه و خطاهای محدودیت Vercel.
4. [ ] **تست DM/Story/Comment:** ۱، ۲ و ۳ checkbox، مصرف مستقل ظرفیت، ذخیره ترتیبی و حالت شکست میانی. آزمون واقعی Meta فقط با مجوز و حساب تست؛ تا آن زمان BLOCKED.
5. [ ] **موبایل/ناوبری:** آیفون Safari و اندروید Chrome در 320..390px، تبلت 768px، Back/Close/Escape/Outside، فرم بلند و checkout، بررسی UX و latency واقعی Login. `docs/runbooks/uat_multichannel_mobile_acceptance_20261015.md`.
6. [ ] **SEO/GA4:** DebugView/Reatime رویداد `page_view`, `signup_intent`, `sign_up` و سیاست robots/noindex UAT با SSO؛ شواهد عملی را جدا از CI ثبت کن.
7. [ ] **Production plan verification فقط read-only:** کاتالوگ واقعی Render و اسنپ‌شات کد/DB Backend فعلی، بدون تغییر allowlist یا Secret. قیمت/دسترسی UAT را به Production تعمیم نده.
8. [ ] **به‌روزرسانی Release Register:** به ازای هر AC، وضعیت PASS/FAIL/BLOCKED، زمان، محیط، evidence و تأیید Owner/Go را ثبت کن.

## P1 — فقط بعد از پذیرش UAT

1. [ ] تعیین میزبانی تجاری مجاز برای Production و بودجه مصرف Neon/Backup؛ بررسی محدودیت Vercel Hobby.
2. [ ] Backup مستقل و قابل بازیابی از Render Production و آزمایش Restore، بررسی Media/jobs/webhooks و مسیر rollback.
3. [ ] Freeze همه Writerها و webhook buffering/dedup + Sync نهایی دیتابیس به Neon Production و برابری تعداد/مبالغ/اشتراک‌ها/رسیدها و اعتبارسنجی مسیر Meta/پرداخت.
4. [ ] تدوین Runbook Cutover/Rollback و گرفتن **GO صریح جداگانه Owner**؛ سپس تنها تغییرات انتخابی مجاز به Production.

## ممنوعیت‌های فعال

- Production `directpilot.ir`، Render API/DB، Neon Production، DNS، Meta callbacks، قیمت واقعی، اشتراک یا پرداخت‌های واقعی را بدون مجوز جدید تغییر نده.
- تاریخچه Snapshot و Git را پاک نکن. پنج فایل کوتاه می‌مانند؛ جزئیات در Release Register/Runbookها و `docs/runbooks/history/20261015_pre_release_register/` هستند.
- PASS شدن CI و Vercel READY را معادل پذیرش UAT یا تأیید انتشار Production اعلام نکن.

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


## P0-07 — Production backup execution preflight (2026-10-15)

- **Confirmed from Render control plane:** Workspace `tea-dabsgm0n74is738av7l0`; production database `directpilot-production-db` (`dpg-db0escm0tbcc73fhig2g-a`), PostgreSQL 16, status `available`, plan `free`, reported expiry **2026-11-02T11:59:46Z**. Production API service `directpilot-api` (`srv-db0f3uc9v7es73b5k51g`) remains on Render.
- **Attempted read-only DB preflight:** `query_render_postgres` could not connect: Render reports **empty IP allowlist blocking all external connections**; hosted Render connector has no fixed IPs for allowlisting. No database-level SQL query was run.
- **Backup outcome: BLOCKED / NOT CREATED. Restore test: NOT RUN.** Available Render connector methods list/read Postgres and execute read-only SQL but do not provide `pg_dump`/snapshot export; never treat schema inspection or copied Neon UAT as a recoverable Production backup.
- **Safe next step:** use a credentialed runtime with authorized private/network DB access to run `pg_dump -Fc` to encrypted durable storage, checksum the archive, then restore to isolated scratch database and validate schema/data counts. Keep source Production unchanged; avoid publishing secrets or raw personal data in GitHub. Do not start P0-08 sync or shutdown until evidence exists.
- **Owner's instruction:** perform work autonomously wherever connected tools permit, without requiring desktop interaction; only request a credential/network authorization if no automated connector route exists. **This entry is an execution blocker, not successful completion.**


## P0-07 — Local Production backup evidence (2026-10-17)

Owner reported successful `pg_dump 16.15 -Fc` against current Render Production database from their Windows computer after restricted network access was restored. Local file: `C:\Users\q\DirectPilotBackups\directpilot_prod_20261017_103343.dump`. A successful `pg_restore --list` confirmed the archive index is readable; SHA-256: `9E46745AA1D115EA74A0877ACEC28A53423ADE73DBEE9FD490842AAFC6D8D064`. **Evidence type: owner-supplied local command output (not an independently inspected file).**

**Stage: BACKUP FILE CREATED / ARCHIVE INDEX PASS; P0-07 OVERALL STILL OPEN.** Full restore test in an isolated scratch database, record-count/schema parity checks, off-device encrypted backup copy and backup recovery plan are still PENDING. Keep local file private; do not upload it to GitHub or chat. No Production schema/data migration, deployment, DNS or service cutover is authorized by this backup evidence. The prior 2026-10-15 BLOCKED note remains as chronological history and is superseded only for backup creation.

## ۲۰۲۶-۱۰-۱۷ — نتیجه واقعی P0-07 و وضعیت انتقال Schema

P0-07: بکاپ واقعی Production و Restore ایزوله روی کامپیوتر Owner **PASS** (۱۷ اکتبر؛ ۸۲ جدول، Alembic 0025، SHA ثبت‌شده در Release Register). UAT Neon **0027/۸۳ جدول** است. Branch فعلی Backend Production تا **0025** Migration دارد؛ 0026/0027 فقط در Branch UAT هستند؛ **اجرای Schema Migration روی Render بدون کد Backend سازگار ممنوع**. آزمون Migration و Backup مستقل خارج از دستگاه هنوز باز است. جزئیات در `docs/releases/RELEASE_REGISTER.md`.
