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
