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
