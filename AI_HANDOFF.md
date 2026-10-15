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
