"""DirectPilot's own service portfolio and consent-based inquiry conversation.

Deterministic content, not an AI agent or universal customer bot builder.
No external calls; examples never make real bookings, payments or accounts.
"""
from dataclasses import dataclass, field
import re

@dataclass(frozen=True)
class Industry:
    id: str
    title: str
    icon: str
    description: str
    features: tuple[str, ...]
    choices: tuple[str, str]
    @property
    def label(self): return self.icon+' '+self.title

CATALOG = (
    Industry('shop','فروشگاه آنلاین','🛍','راهنمای خرید و پیگیری سفارش در یک مسیر ساده.',('نمایش محصولات','دریافت سفارش','پیگیری وضعیت'),('دیدن محصولات','پیگیری سفارش')),
    Industry('food','رستوران و کافه','☕','از دیدن منو تا ثبت درخواست سفارش.',('منوی دسته‌بندی‌شده','انتخاب غذا','درخواست سفارش'),('دیدن منو','سفارش بیرون‌بر')),
    Industry('beauty','سالن زیبایی','💇','معرفی خدمات و دریافت درخواست نوبت.',('معرفی خدمات','انتخاب متخصص','درخواست نوبت'),('خدمات مو','خدمات پوست')),
    Industry('clinic','مطب و کلینیک','🩺','اطلاعات خدمات و هماهنگی نوبت؛ بدون تشخیص پزشکی.',('معرفی خدمات','درخواست نوبت','راهنمای مراجعه'),('درخواست نوبت','راهنمای مراجعه')),
    Industry('education','آموزش و دوره','🎓','معرفی دوره‌ها و دریافت درخواست ثبت‌نام.',('فهرست دوره‌ها','راهنمای انتخاب','درخواست ثبت‌نام'),('دوره‌های آنلاین','کلاس حضوری')),
    Industry('digital','سرویس دیجیتال و VPN','⚡','انتخاب سرویس، پیگیری خرید و تحویل از طریق پنل سازگار.',('معرفی پلن','اتصال به API پنل','تحویل و تمدید'),('انتخاب سرویس','راهنمای اتصال')),
    Industry('property','املاک','🏠','شناخت نیاز متقاضی و هماهنگی بازدید.',('معیارهای جست‌وجو','معرفی فایل','درخواست بازدید'),('خرید ملک','اجاره ملک')),
    Industry('travel','سفر و گردشگری','✈️','معرفی تور و جمع‌آوری درخواست سفر.',('فهرست مقصدها','جزئیات تور','درخواست مشاوره'),('سفر داخلی','سفر خارجی')),
    Industry('hotel','هتل و اقامتگاه','🛎','معرفی اقامتگاه و دریافت درخواست رزرو.',('انواع اتاق','تاریخ سفر','درخواست رزرو'),('دیدن اتاق‌ها','امکانات اقامتگاه')),
    Industry('fitness','باشگاه ورزشی','🏋','معرفی کلاس‌ها و پیگیری درخواست عضویت.',('برنامه کلاس‌ها','معرفی مربی','درخواست عضویت'),('کلاس گروهی','تمرین خصوصی')),
    Industry('repairs','تعمیرات و خدمات','🛠','ثبت مشکل و درخواست هماهنگی کارشناس.',('نوع دستگاه','شرح مشکل','هماهنگی مراجعه'),('تعمیر دستگاه','سرویس دوره‌ای')),
    Industry('automotive','خودرو و کارواش','🚗','معرفی خدمات و هماهنگی مراجعه.',('انتخاب خدمت','درخواست نوبت','پیگیری درخواست'),('سرویس خودرو','شست‌وشوی خودرو')),
    Industry('wholesale','پخش و عمده‌فروشی','📦','دریافت درخواست نمایندگان و پیگیری سفارش.',('کاتالوگ کالا','درخواست سفارش','اتصال به سیستم فروش'),('کاتالوگ عمده','درخواست همکاری')),
    Industry('manufacturing','صنعت و تولید','🏭','معرفی محصولات و دریافت استعلام فنی.',('کاتالوگ فنی','شرح نیاز','درخواست قیمت'),('استعلام محصول','سفارش اختصاصی')),
    Industry('consulting','مشاوره و حقوقی','💼','معرفی حوزه‌های تخصص و هماهنگی جلسه.',('معرفی تخصص‌ها','شرح موضوع','درخواست جلسه'),('جلسه مشاوره','آشنایی با خدمات')),
    Industry('finance','حسابداری و مالی','🧾','معرفی خدمات مالی و دریافت درخواست همکاری.',('خدمات حسابداری','جمع‌آوری نیاز','هماهنگی کارشناس'),('خدمات شرکت‌ها','خدمات اشخاص')),
    Industry('events','رویداد و همایش','🎟','معرفی برنامه و دریافت درخواست ثبت‌نام.',('برنامه رویداد','معرفی سخنران','درخواست ثبت‌نام'),('برنامه رویداد','شرایط شرکت')),
    Industry('media','رسانه و اشتراک','📰','معرفی محتوا و مدیریت درخواست اشتراک.',('دسته‌بندی محتوا','درخواست عضویت','پشتیبانی اشتراک'),('محتوای آموزشی','اشتراک ویژه')),
    Industry('hr','استخدام و منابع انسانی','👥','معرفی فرصت‌ها و دریافت درخواست همکاری.',('فرصت‌های شغلی','دریافت اطلاعات اولیه','پیگیری درخواست'),('فرصت‌های شغلی','معرفی تخصص من')),
    Industry('logistics','حمل‌ونقل و ارسال','🚚','ثبت نیاز حمل و پیگیری درخواست ارسال.',('مبدأ و مقصد','نوع محموله','درخواست هماهنگی'),('ارسال شهری','حمل بین‌شهری')),
    Industry('pets','خدمات حیوانات','🐾','معرفی خدمات و هماهنگی مراجعه.',('معرفی خدمات','درخواست نوبت','راهنمای مراجعه'),('خدمات نگهداری','درخواست نوبت')),
    Industry('charity','خیریه و انجمن','🌱','معرفی فعالیت‌ها و ثبت درخواست همکاری.',('معرفی طرح‌ها','ثبت داوطلب','پرسش‌های رایج'),('همکاری داوطلبانه','آشنایی با طرح‌ها')),
    Industry('technology','فناوری و نرم‌افزار','💻','شناخت نیاز و هماهنگی خدمات فنی.',('شرح مسئله','اتصال به سامانه‌ها','درخواست بررسی'),('پشتیبانی فنی','اتصال نرم‌افزارها')),
    Industry('other','ایدهٔ دیگر','✨','اگر حوزه‌ات اینجا نیست، ایده‌ات را با ما در میان بگذار.',('شرح ایده','بررسی امکان اجرا','پیشنهاد اختصاصی'),('معرفی ایده','شناخت امکانات')),
)
BY_ID = {x.id:x for x in CATALOG}
HOME='🏠 خانه'; BROWSE='🧭 حوزه‌های کسب‌وکار'; ORDER='✍️ درخواست ساخت ربات'; ABOUT='💡 مسیر همکاری'
TRY='▶️ امتحان نمونه'; CHOOSE='✍️ همین مدل را می‌خواهم'; BACK='↩️ بازگشت'; CANCEL='انصراف از درخواست'
CONFIRM='✅ تأیید و ارسال درخواست'; EDIT='✏️ اصلاح توضیحات'; SKIP='همین تلگرام کافی است'
HOME_ROWS=((BROWSE,), (ORDER, ABOUT))
@dataclass
class Reply:
    text: str
    rows: tuple = HOME_ROWS
    state: dict = field(default_factory=dict)
    inquiry: dict | None = None

def catalog_public():
    return [{'id':x.id,'title':x.title,'icon':x.icon,'description':x.description,'features':list(x.features),'choices':list(x.choices)} for x in CATALOG]

def clean_text(s):
    return ''.join(c for c in s.strip() if c in '\n\t' or ord(c)>=32)

def page(number=0):
    number=max(0,min(3,number)); items=CATALOG[number*6:number*6+6]
    rows=tuple(tuple(x.label for x in items[i:i+2]) for i in range(0,len(items),2))
    nav=tuple(x for x in ('⬅️ قبلی' if number else '', 'بعدی ➡️' if number<3 else '') if x)
    return Reply(f'🧭 ربات برای کسب‌وکار شما\n\nحوزه‌ات را انتخاب کن تا ایده‌ها و یک نمونهٔ تعاملی را ببینی.\n\nصفحهٔ {number+1} از ۴ · نمونه‌ها نمایشی‌اند؛ اتصال واقعی پس از بررسی فنی.',rows+(nav, (HOME,)) if nav else rows+((HOME,),),{'step':'browse','page':number})

def details(id):
    x=BY_ID[id]
    return Reply(x.label+'\n\n'+x.description+'\n\nایده‌های قابل بررسی:\n'+'\n'.join('• '+f for f in x.features)+'\n\nنمونه، نمایشی است؛ قیمت و امکان اتصال بعد از بررسی نیاز مشخص می‌شود.',((TRY,), (CHOOSE,), (BROWSE,HOME)),{'step':'detail','industry':id})

def ask_description(id):
    return Reply('✍️ از ایده‌ات بگو\n\nربات چه کاری برای مشتری‌هایت انجام بدهد؟ اگر سایت یا نرم‌افزاری داری، نامش را هم بنویس.\n\n۱۰ تا ۱۲۰۰ کاراکتر کافی است. رمز، توکن یا اطلاعات محرمانه نفرست.\n\nمرحلهٔ ۱ از ۳',((CANCEL,),),{'step':'description','industry':id})

def transition(state, text, username=None):
    text=clean_text(text); step=state.get('step'); industry=state.get('industry','other')
    if industry not in BY_ID: industry='other'
    if text==HOME or text==CANCEL or text.split(' ')[0] in ('/start','/cancel'):
        # Optional start parameter chooses the public portfolio's category.
        param=text.partition(' ')[2]
        if text.startswith('/start ') and param.startswith('idea_') and param[5:] in BY_ID:return details(param[5:])
        return Reply('DIRECTPILOT ✦\nرباتی که برای کار شما ساخته می‌شود.\n\nایده بگیر، یک نمونه را امتحان کن و نیازت را برای بررسی بفرست. این ربات خودش نمونه‌ای از مسیر معرفی خدمات و ثبت درخواست است.\n\nاز کجا شروع کنیم؟')
    if text==BROWSE:return page()
    if text==ABOUT:return Reply('💡 از ایده تا اجرا\n\n۱. حوزه و نیازت را معرفی می‌کنی.\n۲. نیاز را بررسی می‌کنیم و دربارهٔ امکانات، زمان و هزینه به توافق می‌رسیم.\n۳. نسخهٔ آزمایشی می‌سازیـم و با هم تست می‌کنیم.\n۴. پس از تأیید، تحویل و پشتیبانی طبق توافق انجام می‌شود.\n\nثبت درخواست رایگان است و به‌معنای خرید یا قرارداد نیست. پشتیبانی APIها پس از بررسی فنی مشخص می‌شود.')
    if text==ORDER:return page() if step not in ('detail','demo','demo_result') else ask_description(industry)
    if text in ('بعدی ➡️','⬅️ قبلی') and step=='browse':return page(state.get('page',0)+(1 if text=='بعدی ➡️' else -1))
    # During free text entry category labels must remain valid description/contact.
    if step not in ('description','contact','review'):
        selected=next((x for x in CATALOG if text==x.label),None)
        if selected:return details(selected.id)
    if text==BACK:return details(industry)
    if text==CHOOSE:return ask_description(industry)
    if text==TRY:
        x=BY_ID[industry]
        return Reply('🧪 نمونهٔ تعاملی · '+x.title+'\n\nاین فقط نمایش مسیر است؛ سفارش، نوبت، پرداخت یا حساب واقعی ایجاد نمی‌کند.\n\nیکی از گزینه‌ها را امتحان کن:',(x.choices,(CHOOSE,), (BACK,HOME)),{'step':'demo','industry':industry})
    if step=='demo' and text in BY_ID[industry].choices:
        return Reply('🧪 نتیجهٔ نمونه\n\nانتخاب شما: '+text+'\n\nدر ربات اختصاصی، این مرحله می‌تواند اطلاعات لازم را دریافت کند و به مسیر مربوط هدایت شود. اتصال و نتیجهٔ واقعی به نیاز و سامانهٔ شما بستگی دارد.\n\nبرای کسب‌وکارت چنین مسیری می‌خواهی؟',((CHOOSE,), (TRY,BACK), (HOME,)),{'step':'demo_result','industry':industry})
    if step=='description':
        if not 10<=len(text)<=1200:return Reply('لطفاً نیازت را در ۱۰ تا ۱۲۰۰ کاراکتر بنویس؛ رمز یا توکن نفرست.',((CANCEL,),),state)
        s={'step':'contact','industry':industry,'description':text}
        return Reply('📨 چطور با تو هماهنگ کنیم؟\n\nنام و راه ارتباطی دلخواهت را بنویس، یا «همین تلگرام کافی است» را بزن. شمارهٔ تماس اجباری نیست.\n\nمرحلهٔ ۲ از ۳',((SKIP,), (CANCEL,)),s)
    if step=='contact':
        if not 2<=len(text)<=120:return Reply('راه ارتباطی را در ۲ تا ۱۲۰ کاراکتر بنویس یا از همین تلگرام استفاده کن.',((SKIP,), (CANCEL,)),state)
        s={**state,'step':'review','contact':('@'+username if username and re.fullmatch(r'[A-Za-z0-9_]{5,32}',username) else 'گفت‌وگو در همین تلگرام') if text==SKIP else text}
        return review(s)
    if step=='review':
        if text==EDIT:return ask_description(industry)
        if text==CONFIRM:
            data={k:state[k] for k in ('industry','description','contact')}
            return Reply('درخواست برای ثبت آماده است.',inquiry=data)
        return review(state)
    return Reply('از دکمه‌های زیر شروع کن. برای ثبت نیاز، اول حوزهٔ کسب‌وکارت را انتخاب کن.',state=state)

def review(s):
    return Reply('🔎 مرور درخواست\n\nحوزه: '+BY_ID[s['industry']].title+'\n\nنیاز شما:\n'+s['description']+'\n\nراه ارتباطی: '+s['contact']+'\n\nبا تأیید، این اطلاعات و شناسهٔ تلگرام شما برای بررسی و پیگیری در اختیار تیم DirectPilot قرار می‌گیرد. هیچ خرید یا پرداختی انجام نمی‌شود.\n\nمرحلهٔ ۳ از ۳',((CONFIRM,), (EDIT,CANCEL)),s)
