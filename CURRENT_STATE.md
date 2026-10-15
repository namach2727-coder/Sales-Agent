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
