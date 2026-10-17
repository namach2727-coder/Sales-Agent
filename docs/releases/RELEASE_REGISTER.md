# DirectPilot — Release Register (مرجع واحد انتشار)

**آخرین تطبیق مستنداتی:** 2026-10-15 | **دامنه UAT:** https://uat.directpilot.ir | **دامنه Production:** https://directpilot.ir

این ثبت، **وضعیت واقعی استقرار** را از **وجود کد**، **PASS تست خودکار**، **تأیید کسب‌وکار** و **اجازه انتقال Production** جدا می‌کند. تاریخچه اصلی بدون حذف در `docs/runbooks/history/20261015_pre_release_register/` نگهداری شده است. هیچ سطر این جدول مجوز انتشار Production نیست.

## قرارداد وضعیت و تأیید

- **UAT-CODE**: کد در Branch `UAT` یا Backend مخصوص UAT وجود دارد؛ **UAT-DEPLOY**: commit متناظر روی دامنه رسمی UAT مستقر و READY شده؛ **CI-PASS**: تست خودکار موفق؛ **UAT-BROWSER-PENDING**: تست مرورگر واقعی/کاربر هنوز کامل نیست.
- **PROD-DEPLOY-CODE**: کد مربوط در **SHA واقعاً متصل به alias Production** یافت شده؛ **PROD-PR**: PR به `main` ادغام شده، ولی اجرای کسب‌وکاری جدا از آن است؛ **PROD-ABSENT**: در SHA فعال Production، کد قابلیت وجود ندارد؛ **PROD-UNVERIFIED**: شواهد کافی برای اعلام پیاده‌سازی یا سلامت عملیاتی نداریم.
- **OWNER-DOC-APPROVED** یعنی کاربر در 2026-10-15 شش اصلاح **مستنداتی** را تأیید کرده است، نه تأیید UAT هر قابلیت یا GO برای Production. همه ردیف‌های نیازمند UAT واقعی با **OWNER-UAT-PENDING** باقی می‌مانند.
- وضعیت قابلیت تنها با PR کافی نیست: وجود در SHA استقرار، کنترل دامنه، نیازهای دیتابیس/Backend و تست end-to-end جداگانه ضروری است.

## شواهد استقرار مرجع

| محیط | Frontend و GitHub | Backend و Database | سطح شواهد |
|---|---|---|---|
| UAT | `directpilot-web`, Branch `UAT`, SHA `dad3a3790246f96fbbe760d26e2415afd0a45851`, Vercel `dpl_GGgg4EkaQF3bExfnzbfgRBK1GLhj` READY | `directpilot-uat-api.vercel.app`, Branch `migration/vercel-uat-fastapi-20261014`, مستقل از Production؛ Neon `round-shape-42044596/neondb`, Alembic `0027_traceable_receipt_versions` | CI و HTTP smoke PASS؛ موبایل/رسید/Meta end-to-end کامل نیست |
| Production | `directpilot-web`, Branch `main`, SHA `8592c6e91d4beaed7c31653dc285612fd511fa53`, Vercel `dpl_cRZsk7rndqFWH1KnKdhLVbNU1VxF` READY | Render `directpilot-api` و دیتابیس مرجع Render؛ با Neon UAT یکی نیست | وجود کد Frontend و PRهای Production بررسی‌شده؛ DB واقعی Render از این اتصال تأیید مستقیم نشده؛ هیچ cutover صورت نگرفته است |

> وضعیت این جدول snapshot است. برای تصمیم انتشار بعدی، alias و commit و نسخه migration را همان لحظه دوباره استعلام کنید. **مرجع Production پایگاه داده فعلی Render است؛ Neon Production هنوز همگام‌سازی نهایی تأییدشده ندارد.**

## ثبت قابلیت‌ها و انتشارها — ۸ تا ۱۵ اکتبر

| شناسه | PR منبع (F=Frontend، B=Backend) | قابلیت/خروجی مشخص | UAT | Production | تأیید کاربر |
|---|---|---|---|---|---|
| REL-001 | F#1–#5, F#30 | بهبود سئو، لینک‌سازی داخلی و انتشار مقاله Smart Direct | کد مشترک/بخشی از UAT؛ آزمون سئوی عملی جدا | **PROD-PR / PROD-DEPLOY-CODE** در `main`؛ نتیجه رتبه‌بندی/ایندکس جداگانه سنجیده نشده | OWNER-DOC-APPROVED؛ KPI نیازمند اندازه‌گیری |
| REL-002 | F#6–#8 | GA4 consent، اصلاح CSP و صف gtag | اثر روی Production source ثابت است؛ نتیجه Realtime مستقل | **PROD-PR**؛ رخدادهای `page_view`, `signup_intent`, `sign_up` بدون شواهد لحظه‌ای PASS محسوب نمی‌شوند | اندازه‌گیری PENDING |
| REL-003 | F#9 | Humanized UI و motion | تغییر طراحی ادغام‌شده | **PROD-PR**؛ ارزیابی دیداری/دسترس‌پذیری جداست | UI acceptance PENDING |
| REL-004 | F#10, F#20 | ثبت‌نام→داشبورد→انتخاب پلن→سفارش→کارت‌به‌کارت→رسید | UAT-DEPLOY؛ E2E سناریوی کامل PENDING | **PROD-PR / code present** در انتشار F#20؛ تراکنش واقعی و پرداخت تأییدشده از این ممیزی اثبات نشده | OWNER-UAT-PENDING |
| REL-005 | F#11, F#20 | توضیح تفکیکی پلن‌ها، CTA و نمایش مشخصات کارت | UAT-DEPLOY؛ UX مشتری PENDING | **PROD-PR / code present**؛ نمایش کارت، کپی و مسیر پرداخت در SHA Production دیده شده | OWNER-UAT-PENDING |
| REL-006 | F#12 | انتخاب هم‌زمان **DM / Story / Comment**، حفظ اسکرول انتخاب پلن و تمایز AI | **UAT-DEPLOY / CI-PASS**؛ Meta end-to-end PENDING | **PROD-ABSENT** در کامپوننت انتخاب trigger نسخه فعال | OWNER-UAT-PENDING؛ نیازمند GO مستقل |
| REL-007 | F#15, F#16, F#20 | خرید **۱ تا ۱۲ ماهه** پلن پولی ۳۰روزه؛ مبلغ و مدت snapshot سفارش | **UAT-DEPLOY / CI-PASS**؛ بررسی مالی واقعی PENDING | **PROD-DEPLOY-CODE**: فراخوانی `ordersApi.create(id,months)` در SHA فعال Production تأیید شد؛ E2E مالی مستقل | OWNER-UAT-PENDING |
| REL-008 | F#17, F#18, F#20 | پیش‌نمایش امن JPEG/PNG/PDF رسید در ادمین، صفحه پرداخت جمع‌وجور، CTA ارتقا، کپی شماره کارت | **UAT-DEPLOY / CI-PASS**؛ مسیر حقیقی پرداخت PENDING | **PROD-DEPLOY-CODE** برای فرم‌ها/کپی و PR انتشار F#20؛ پذیرش نسخه‌های تاریخی شامل این ردیف نیست | OWNER-UAT-PENDING |
| REL-009 | F#21, F#22 | رفع پوشانده‌شدن ورود با منوی موبایل در نسخه اولیه | **UAT-DEPLOY** | **PROD-PR** F#22؛ اصلاح کامل جدید REL-016 نیست | مرورگر موبایل PENDING |
| REL-010 | F#23, F#24, F#25 | ساده‌سازی داشبورد مشتری و حذف نمایش مکالمات آنلاین | **UAT-DEPLOY** | **PROD-PR** F#25؛ عدم بازگشت پنل مکالمات باید در مرورگر تأیید شود | OWNER-UAT-PENDING |
| REL-011 | F#26, F#29 | محتوای Features/Solutions و انتشار مرکز راهکارها | **UAT-DEPLOY** | **PROD-PR** F#29؛ صفحه عمومی `/solutions` در `main` ثبت شده | محتوای عمومی نیازمند بازبینی نهایی |
| REL-012 | F#27, F#28, F#31 | اصلاح پیام دوره آزمایشی از ادعای ۱۴ روز به **۳ روز** و سپس تبدیل متن پلن به داده واقعی Backend | **UAT-DEPLOY**؛ جدول دیتابیس و قواعد `trial_eligible` پایین، نه متن تبلیغاتی ثابت | **PROD-PR** F#27 (پیام ۳روز)؛ همسانی کاتالوگ/نحوه فعال‌سازی Production **PROD-UNVERIFIED** | تعیین متن نهایی و تست Signup PENDING |
| REL-013 | B#34 | ذخیره تصاویر محصول با `product_media_assets.image_data BYTEA`، محدودیت ۲ MiB/تصویر و ۵۰ MiB/فروشگاه | **UAT-CODE/SCHEMA/DEPLOY**؛ تست واقعی آپلود/حذف/پایداری PENDING | **PROD-ABSENT / NOT CUT OVER**؛ PR به UAT Backend محدود بود | OWNER-UAT-PENDING |
| REL-014 | B#36, F#31 | **رسید نسخه‌دار** با اتصال مشتری/سفارش/پرداخت، جست‌وجوی ایمیل/تاریخ، سابقه ادمین، SHA-256 | **UAT-DEPLOY/DB 0027؛ ۲/۲ receipt backfill PASS**؛ Browser E2E و backup مستقل PENDING | **PROD-ABSENT / PROD-UNVERIFIED**؛ تاریخچه قبلی را در Production بدون شواهد فرض نکنید | OWNER-UAT-PENDING |
| REL-015 | F#31 | اصلاح «بررسی حساب» بدون بلوکه‌کردن فرم ورود و محافظت در برابر `/auth/me` دیرهنگام | **UAT-DEPLOY / CI-PASS**؛ اندازه‌گیری سرعت روی گوشی PENDING | **PROD-ABSENT** برای UX جدید در کد فعلی فرم ورود | OWNER-UAT-PENDING |
| REL-016 | F#32 | بازطراحی ناوبری موبایل مشتری/ادمین/عمومی؛ Back و Close، Escape، Touch، Safe-area و فرم‌ها | **UAT-DEPLOY / ۲۲۳ تست PASS**؛ iPhone/Android دستی PENDING | **PROD-ABSENT** برای منوی مشترک جدید | OWNER-UAT-PENDING |
| REL-017 | B#31, B#38–#43 | انتقال Backend UAT به Vercel + Neon و حفاظت/تست دامنه `uat.directpilot.ir` | **UAT Backend READY، /ready و routing PASS**؛ UAT business signoff هنوز باز | **NOT A PRODUCTION RELEASE**؛ Render همچنان مرجع | GO Production داده نشده |
| REL-018 | B#33 (بسته)، B#35, B#37 | تصمیم دائمی **PostgreSQL BYTEA؛ عدم استفاده از R2/S3** و رد پیاده‌سازی آزمایشی Storage خارجی | ثبت در مستندات؛ UAT migration مطابق تصمیم | تغییر Production در این تصمیم اعمال نشده | **تصمیم معماری تأییدشده** |
| REL-019 | F#31, B#36 | الزام بازیابی رسیدهای هر مشتری **پس از چهار ماه و حتی بعد از جایگزینی رسید ردشده** | مدل و تست ۱۲۵ روزه در کد؛ آزمون Backup و بازیابی بلندمدت PENDING | **NOT VERIFIED / NOT PROMOTED** | الزام محصول تأیید شده، SLA عملیاتی هنوز نه |
| REL-020 | F#20, F#25, F#29, F#30 | انتشارهای مستقل و انتخابی Frontend Production طی ۱۲ تا ۱۴ اکتبر | ثبت صرفاً به‌عنوان شاهد انتشار انتخابی | **PROD-PR**؛ انتشارهای قبلی را دوباره مهاجرت ندهید | تأیید انتشار گذشته ≠ UAT همه قابلیت‌ها |

لینک‌های PR در GitHub:
- Frontend: `https://github.com/namach2727-coder/directpilot-web/pull/<number>`
- Backend: `https://github.com/namach2727-coder/Sales-Agent/pull/<number>`

## کاتالوگ واقعی UAT — Snapshot فقط‌خواندنی Neon، ۱۵ اکتبر

**Source of truth:** `neondb.public.saas_plans`؛ نوع پول **IRR**، مبالغ به **ریال** هستند؛ تمام اطلاعات زیر از داده واقعی UAT هستند، **نه Production**.

| کد | نوع | قیمت دوره (ریال) | روز | وضعیت فعال | قابل خرید | مجاز برای Trial | سقف اتوماسیون | سهمیه پاسخ/AI | اکانت Instagram |
|---|---|---:|---:|---|---|---|---:|---|---:|
| `AUTOMATION_TRIAL` | Automation | ۰ | ۳ | بله | خیر | **بله** | ۳ | پاسخ ۰، AI — | ۱ |
| `AI_ASSISTANT_TRIAL` | AI Assistant | ۰ | ۳ | بله | خیر | **بله** | ۰ | پاسخ ۲۰۰، AI request نامشخص | ۱ |
| `AUTOMATION_V1` | Automation | ۴٬۹۰۰٬۰۰۰ | ۳۰ | بله | **بله** | خیر | ۲۰ | پاسخ ۰، AI — | ۱ |
| `AI_ASSISTANT_V1` | AI Assistant | ۶٬۹۰۰٬۰۰۰ | ۳۰ | بله | **بله** | خیر | ۰ | پاسخ ۱۰۰۰، AI request ۱۰۰۰ | ۱ |
| `START` | legacy | ۲٬۹۹۰٬۰۰۰ | ۳۰ | بله | **خیر** | خیر | ۱۰ | پاسخ ۱۵۰۰ | ۱ |
| `PRO` | legacy | ۶٬۹۹۰٬۰۰۰ | ۳۰ | بله | **خیر** | خیر | ۳۰ | پاسخ ۵۰۰۰ | ۱ |
| `TRIAL` | legacy | ۰ | ۳ | بله | **خیر** | **خیر** | ۳ | پاسخ ۲۰۰ | ۱ |
| `FREE` | legacy | ۰ | — | **خیر** | **خیر** | خیر | ۱ | پاسخ ۲۰ | ۱ |

- **فعال‌بودن** معادل **قابل خرید بودن** نیست؛ `START`, `PRO` و `TRIAL` ممکن است به دلیل سابقه برای خواندن داده باقی بمانند و نباید در UI خرید آزاد نمایش داده شوند.
- فقط دو طرح تخصصی `*_TRIAL` دارای `trial_eligible=true` و مدت سه روزند. عبارت «همه پلن‌ها سه روز رایگان» بدون بررسی سیاست ثبت‌نام ممنوع است.
- قیمت، مدت، محدودیت و کد هر پلن باید از Backend و `saas_plans` خوانده شود؛ تغییرات و Snapshot سفارش بر قیمت آینده اثر پس‌نگر ندارد. به‌روزرسانی کاتالوگ نیازمند تصمیم تجاری مستقل است.
- **Production catalog not verified:** هیچ عدد این جدول مبنای ادعای مقدار دیتابیس فعلی Render نیست.

## تعریف دقیق قابلیت چندکاناله

در Frontend UAT، کاربر می‌تواند **یک، دو یا سه** گزینه مستقل `DM_KEYWORD`, `STORY_REPLY_KEYWORD`, `COMMENT_KEYWORD` را به‌صورت checkbox انتخاب کند، اما **Backend یک Rule مشترک چند trigger ندارد**. UI برای هر کانال **یک قانون مستقل** به‌صورت ترتیبی می‌سازد و هرکدام **یک واحد از ظرفیت پلن** مصرف می‌کند. برای DM و Story اکشن `SEND_MESSAGE` و برای Comment اکشن `SEND_PRIVATE_MESSAGE` ثبت می‌شود. باید دست‌کم یک کانال انتخاب شود و ظرفیت قبل از ارسال کنترل شود. در صورت موفقیت ناقص، UI فهرست را Refresh و از تکرار کورِ کل عملیات منع می‌کند؛ **این عملیات اتمیک نیست**. ویرایش قانون موجود فقط اولین trigger انتخابی را آپدیت و برای انتخاب‌های اضافی Rule جدید می‌سازد. آزمون واقعی Meta webhook/send همچنان **BLOCKED/PENDING** است؛ CI صرفاً قرارداد کد را ثابت می‌کند.

## معیارهای پذیرش و انتقال

جزئیات گام‌به‌گام در این Runbookها:
- `docs/runbooks/uat_customer_billing_acceptance_20261015.md`
- `docs/runbooks/uat_multichannel_mobile_acceptance_20261015.md`
- `docs/runbooks/uat_mobile_frontend_ux_audit_20261015.md`
- `docs/runbooks/official_uat_acceptance_gate_20261014.md`

**صریحاً PENDING:** UAT موبایل Safari/Chrome، انتخاب سه کانال با ظرفیت واقعی، DM/Story/Comment Meta E2E، خرید ۱ تا ۱۲ ماه، عکس رسید با آپلود/بازآپلود و نسخه‌ها، پذیرش ادمین، بازیابی مستقل چهارماهه، GA4 Realtime و صحت کاتالوگ Production.

**Hard stop Production:** هیچ merge از کل `UAT` به `main`، هیچ ایجاد Deployment، تغییر Render/Neon Production، DNS، Meta، پرداخت واقعی، فعال‌سازی دستی اشتراک یا قطع سرویس انجام نشود تا owner جداگانه GO دهد و backup/freeze/parity/rollback و eligibility میزبانی تجاری اثبات شوند.

## روش نگهداری

۱. در هر تغییر PR/Deploy، فقط ردیف مرتبط را با **شماره PR، commit/deployment، وضعیت UAT، Production و تأیید مشتری** اصلاح کنید. ۲. برای PASS عملی، نتیجه تست با زمان، محیط و شواهد ثبت شود. ۳. پنج فایل بالا صرفاً خلاصه و لینک باشند؛ تکرار تاریخچه در هر پنج فایل ممنوع. ۴. تاریخچه اصلی دقیقاً در `docs/runbooks/history/20261015_pre_release_register/` و Git باقی بماند؛ پاک‌سازی آن ممنوع.

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
