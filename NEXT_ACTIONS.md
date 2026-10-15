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
