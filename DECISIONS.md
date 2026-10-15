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

## تصمیم‌های باز؛ نباید قطعی تفسیر شوند

- قیمت‌های Production Render و تفاوت با کاتالوگ Neon UAT: **UNVERIFIED**، جدول UAT مجوز تغییر Production نیست.
- ساختار Atomic batch یا گروه‌بندی ظاهری Ruleهای سه‌کاناله، موتور Meta و انتشار واقعی: **NOT DECIDED / E2E PENDING**.
- SLA عملیاتی ۱۲ماهه و Backup off-provider با Restore دوره‌ای: **PENDING**.
- نوع پلن تجاری Vercel/میزبان نهایی Production و زمان cutover: **PENDING**.

**جزئیات تاریخی و چرایی تصمیم‌ها** دست‌نخورده در Runbookهای پیشین، Archive و Git باقی مانده‌اند؛ این سند جای تاریخچه طولانی نیست.
