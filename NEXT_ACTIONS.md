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
