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
