import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.catalog_runtime import (
    find_knowledge_answer as find_catalog_knowledge_answer,
    list_products as list_catalog_products,
    resolve_product as resolve_catalog_product,
)
from app.catalog_text import normalize_catalog_text
from app.models import Conversation, Customer, FAQ, Order, Product
from app.schemas import ChatRequest


PRODUCT_ALIASES = [
    ("قاب سیلیکونی iPhone 15", ("قاب", "کاور")),
    ("Apple iPhone 15 128GB", ("iphone 15", "آیفون 15", "آیفون", "ایفون")),
    ("Samsung Galaxy A55 256GB", ("a55", "galaxy", "سامسونگ", "اندروید")),
]

FINGLISH_REPLACEMENTS = (
    ("che mahsoolati darid", "چه محصولاتی دارید"),
    ("che mahsulati darid", "چه محصولاتی دارید"),
    ("sefaresh mano sabt kon", "سفارش من را ثبت کن"),
    ("sefaresham ro sabt kon", "سفارشم را ثبت کن"),
    ("sefareshe mano sabt kon", "سفارش من را ثبت کن"),
    ("ba man tamas begirid", "با من تماس بگیرید"),
    ("ba operator sohbat konam", "با اپراتور صحبت کنم"),
    ("mikham bekharam", "میخوام بخرم"),
    ("mikhaham bekharam", "میخواهم بخرم"),
    ("baram kenar bezar", "برام کنار بذار"),
    ("gheymatesh chande", "قیمتش چنده"),
    ("gheymat chand", "قیمت چند"),
    ("sefareshamo", "سفارشم را"),
    ("sefaresham", "سفارشم"),
    ("safareshamo", "سفارشم را"),
    ("safaresham", "سفارشم"),
    ("sabt kon", "ثبت کن"),
    ("reserve kon", "رزرو کن"),
    ("rezerv kon", "رزرو کن"),
    ("chi darid", "چی دارید"),
    ("che darid", "چه دارید"),
    ("vaght bekheir", "وقت بخیر"),
    ("sobh bekheir", "صبح بخیر"),
    ("shab bekheir", "شب بخیر"),
    ("kart be kart", "کارت به کارت"),
    ("kharid hozoori", "خرید حضوری"),
    ("saat kari", "ساعت کاری"),
    ("forushgah kojast", "فروشگاه کجاست"),
    ("khoda hafez", "خداحافظ"),
    ("gheymat", "قیمت"),
    ("geymat", "قیمت"),
    ("qeymat", "قیمت"),
    ("iphone", "آیفون"),
    ("samsung", "سامسونگ"),
    ("android", "اندروید"),
    ("ghab", "قاب"),
    ("cover", "قاب"),
    ("sefaresh", "سفارش"),
    ("sefares", "سفارش"),
    ("safaresh", "سفارش"),
    ("haminja", "همینجا"),
    ("mikham", "میخوام"),
    ("mikhaham", "میخواهم"),
    ("bekharam", "بخرم"),
    ("kharid", "خرید"),
    ("operator", "اپراتور"),
    ("operater", "اپراتور"),
    ("moshaver", "مشاور"),
    ("moshavar", "مشاور"),
    ("poshtiban", "پشتیبان"),
    ("karshenas", "کارشناس"),
    ("tamas", "تماس"),
    ("shomare", "شماره"),
    ("mobile", "موبایل"),
    ("ersal", "ارسال"),
    ("ersaal", "ارسال"),
    ("peyk", "پیک"),
    ("garanti", "گارانتی"),
    ("garantee", "گارانتی"),
    ("zemanat", "ضمانت"),
    ("pardakht", "پرداخت"),
    ("takhfif", "تخفیف"),
    ("arzoontar", "ارزونتر"),
    ("arzountar", "ارزونتر"),
    ("ghest", "قسط"),
    ("aghsat", "اقساط"),
    ("registry", "رجیستری"),
    ("register", "رجیستری"),
    ("hamta", "همتا"),
    ("asalat", "اصالت"),
    ("asli", "اصل هست"),
    ("fake", "فیک"),
    ("marjoo", "مرجوع"),
    ("marjooei", "مرجوعی"),
    ("taviz", "تعویض"),
    ("adres", "آدرس"),
    ("forushgah", "فروشگاه"),
    ("kojast", "کجاست"),
    ("saat", "ساعت"),
    ("mamnoon", "ممنون"),
    ("mamnun", "ممنون"),
    ("merci", "مرسی"),
    ("mersi", "مرسی"),
    ("tnx", "ممنون"),
    ("khodahafez", "خداحافظ"),
    ("bye", "خداحافظ"),
    ("mahsool", "محصول"),
    ("mahsul", "محصول"),
    ("mojood", "موجود"),
    ("mojud", "موجود"),
    ("rang", "رنگ"),
    ("moshakhasat", "مشخصات"),
    ("hafeze", "حافظه"),
    ("salam", "سلام"),
    ("dorood", "درود"),
)

AUTO_RESPONSE_RULES = [
    (
        ("تخفیف", "ارزونتر", "ارزانتر", "آخرش چند", "قیمت آخر"),
        "قیمت‌های این دمو ثابت هستند؛ برای تخفیف ویژه می‌توانم درخواست شما را به اپراتور فروش ارجاع دهم.",
    ),
    (
        ("قسط", "اقساط", "چکی"),
        "خرید اقساطی در نسخه آزمایشی فعال نیست؛ شرایط واقعی باید توسط اپراتور فروش تأیید شود.",
    ),
    (
        ("رجیستر", "رجیستری", "همتا"),
        "موبایل‌های این دمو رجیسترشده و قابل انتقال در سامانه همتا در نظر گرفته شده‌اند.",
    ),
    (
        ("اصل هست", "اصالت", "فیک", "تقلبی"),
        "همه محصولات این دمو اصل و دارای ضمانت اصالت فرض شده‌اند.",
    ),
    (
        ("ساعت کاری", "چه ساعتی", "کی باز", "کی پاسخ"),
        "پاسخ‌گویی خودکار شبانه‌روزی است؛ اپراتور آزمایشی از ساعت ۹ تا ۱۸ پیگیری می‌کند.",
    ),
    (
        ("آدرس", "فروشگاه کجاست", "خرید حضوری", "حضوری بیام"),
        "این فروشگاه فعلاً یک دموی آنلاین است و نشانی حضوری واقعی ندارد.",
    ),
    (
        ("ممنون", "مرسی", "تشکر", "دمت گرم"),
        "خواهش می‌کنم 🌱 اگر محصولی را انتخاب کرده‌اید، می‌توانم همین‌جا سفارش آزمایشی آن را ثبت کنم.",
    ),
    (
        ("خداحافظ", "فعلا", "روز خوش"),
        "روز خوبی داشته باشید. هر زمان برگشتید، ادامه گفتگو و سفارش شما در سیستم باقی می‌ماند.",
    ),
]


def normalize_text(value: str) -> str:
    normalized = (
        normalize_catalog_text(value.replace("‌", ""))
        .replace("سقارش", "سفارش")
        .replace("سفارس", "سفارش")
        .replace("سغارش", "سفارش")
    )
    for finglish, persian in sorted(FINGLISH_REPLACEMENTS, key=lambda item: len(item[0]), reverse=True):
        pattern = rf"(?<![a-z0-9]){re.escape(finglish)}(?![a-z0-9])"
        normalized = re.sub(pattern, persian, normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def contains_any(message: str, phrases: tuple[str, ...]) -> bool:
    return any(phrase in message for phrase in phrases)


def extract_phone(message: str) -> str | None:
    normalized = normalize_text(message)
    compact = re.sub(r"[\s\-()]", "", normalized)
    match = re.search(r"(?<!\d)(?:\+98|0098|98|0)?9\d{9}(?!\d)", compact)
    if not match:
        return None

    phone = match.group(0)
    if phone.startswith("+98"):
        return "0" + phone[3:]
    if phone.startswith("0098"):
        return "0" + phone[4:]
    if phone.startswith("98"):
        return "0" + phone[2:]
    if phone.startswith("9"):
        return "0" + phone
    return phone


def find_product(
    db: Session, message: str, store_slug: str = "default"
) -> Product | None:
    resolution = resolve_catalog_product(db, message, store_slug)
    if resolution.managed:
        return resolution.product

    normalized = normalize_text(message)
    for product_name, aliases in PRODUCT_ALIASES:
        if any(alias in normalized for alias in aliases):
            return db.scalar(
                select(Product)
                .where(Product.name == product_name)
                .order_by(Product.id)
            )
    return None


def find_recent_product(
    db: Session, customer_id: int, store_slug: str = "default"
) -> Product | None:
    conversations = db.scalars(
        select(Conversation)
        .where(Conversation.customer_id == customer_id)
        .order_by(Conversation.id.desc())
        .limit(10)
    ).all()
    for conversation in conversations:
        product = find_product(db, conversation.user_message, store_slug)
        if product:
            return product
    return None


def find_faq_answer(db: Session, message: str) -> str | None:
    normalized = normalize_text(message)
    keyword_map = {
        "ارسال": "ارسال",
        "پست": "ارسال",
        "پیک": "ارسال",
        "چند روز": "ارسال",
        "گارانتی": "گارانتی",
        "ضمانت": "گارانتی",
        "پرداخت": "پرداخت",
        "کارت به کارت": "پرداخت",
        "در محل": "پرداخت",
        "مرجوع": "مرجوعی",
        "تعویض": "مرجوعی",
    }
    for user_keyword, faq_keyword in keyword_map.items():
        if user_keyword in normalized:
            faq = db.scalar(
                select(FAQ).where(FAQ.question.contains(faq_keyword), FAQ.is_active.is_(True))
            )
            if faq:
                return faq.answer
    return None


def format_price(price: float) -> str:
    return f"{price:,.0f} تومان"


def is_order_intent(message: str) -> bool:
    normalized = normalize_text(message)
    return contains_any(
        normalized,
        (
            "سفارش",
            "ثبتش کن",
            "بخرمش",
            "میخوام بخرم",
            "میخواهم بخرم",
            "خرید کنم",
            "برام کنار بذار",
            "برای من کنار بذار",
            "رزرو کن",
        ),
    )


def is_operator_intent(message: str) -> bool:
    normalized = normalize_text(message)
    return contains_any(
        normalized,
        ("اپراتور", "مشاور", "پشتیبان", "کارشناس", "تماس بگیرید", "تماس بگیر", "شکایت", "مشکل"),
    )


def order_to_dict(order: Order) -> dict:
    return {
        "id": order.id,
        "customer_id": order.customer_id,
        "customer_name": order.customer.name,
        "phone": order.customer.phone,
        "product_id": order.product_id,
        "product_name": order.product.name,
        "quantity": order.quantity,
        "unit_price": order.unit_price,
        "total_price": order.unit_price * order.quantity,
        "status": order.status,
        "created_at": order.created_at,
    }


def handle_order(
    db: Session,
    customer: Customer,
    message: str,
    store_slug: str = "default",
) -> tuple[str, Product | None, bool, Order | None]:
    resolution = resolve_catalog_product(db, message, store_slug)
    if resolution.managed and resolution.ambiguous:
        names = "، ".join(product.name for product in resolution.candidates)
        return (
            f"منظورتان کدام محصول است: {names}؟",
            None,
            False,
            None,
        )

    product = (
        resolution.product
        if resolution.managed
        else find_product(db, message, store_slug)
    )
    product = product or find_recent_product(db, customer.id, store_slug)
    if product is None:
        managed, products = list_catalog_products(db, store_slug)
        if products:
            names = "، ".join(product.name for product in products)
            prompt = f"حتماً. اول مشخص کنید کدام محصول را می‌خواهید: {names}؟"
        elif managed:
            prompt = "فعلاً محصول منتشرشده‌ای برای ثبت سفارش وجود ندارد."
        else:
            prompt = "حتماً. اول مشخص کنید کدام محصول را می‌خواهید."
        return (
            prompt,
            None,
            False,
            None,
        )

    if not product.is_available:
        return "این محصول فعلاً موجود نیست و امکان ثبت سفارش آن وجود ندارد.", product, False, None

    if not customer.phone:
        return (
            f"برای ثبت سفارش {product.name} لطفاً شماره موبایل خود را بفرستید؛ مثلاً ۰۹۱۲۱۲۳۴۵۶۷.",
            product,
            False,
            None,
        )

    existing_order = db.scalar(
        select(Order)
        .where(
            Order.customer_id == customer.id,
            Order.product_id == product.id,
            Order.status == "pending",
        )
        .order_by(Order.id.desc())
    )
    if existing_order:
        return (
            f"این سفارش قبلاً با شماره #{existing_order.id} ثبت شده و در انتظار پیگیری اپراتور است.",
            product,
            True,
            existing_order,
        )

    order = Order(
        customer=customer,
        product=product,
        quantity=1,
        unit_price=product.price,
        status="pending",
    )
    db.add(order)
    db.flush()
    return (
        f"سفارش آزمایشی شما برای {product.name} با شماره #{order.id} ثبت شد. "
        f"مبلغ {format_price(product.price)} است و اپراتور برای تأیید نهایی تماس می‌گیرد؛ هنوز پرداختی انجام نشده است.",
        product,
        True,
        order,
    )


def build_reply(
    db: Session,
    customer: Customer,
    message: str,
    store_slug: str = "default",
) -> tuple[str, Product | None, bool]:
    normalized = normalize_text(message)

    if is_operator_intent(normalized):
        if customer.phone:
            return "درخواست ارتباط با اپراتور ثبت شد. اپراتور با شماره ذخیره‌شده شما تماس می‌گیرد.", None, True
        return "حتماً. برای تماس اپراتور لطفاً شماره موبایل خود را بفرستید.", None, False

    managed_knowledge, knowledge_answer = find_catalog_knowledge_answer(
        db, message, store_slug
    )
    if managed_knowledge:
        if knowledge_answer:
            return knowledge_answer, None, False
    else:
        faq_answer = find_faq_answer(db, normalized)
        if faq_answer:
            return faq_answer, None, False

        for triggers, response in AUTO_RESPONSE_RULES:
            if contains_any(normalized, triggers):
                return response, None, False

    resolution = resolve_catalog_product(db, message, store_slug)
    if resolution.managed and resolution.ambiguous:
        names = "، ".join(product.name for product in resolution.candidates)
        return f"منظورتان کدام محصول است: {names}؟", None, False

    product = (
        resolution.product
        if resolution.managed
        else find_product(db, message, store_slug)
    )
    if contains_any(normalized, ("رنگ", "مشخصات", "حافظه")):
        product = product or find_recent_product(db, customer.id, store_slug)
        if product:
            return product.description or "توضیحات بیشتری برای این محصول ثبت نشده است.", product, False

    if product:
        availability = "موجود است" if product.is_available else "فعلاً موجود نیست"
        price_label = "قیمت آن" if resolution.managed else "قیمت فرضی آن"
        reply = (
            f"{product.name} {availability}. {price_label} {format_price(product.price)} است. "
            "برای خرید بنویسید «سفارشم را ثبت کن» یا شماره موبایل خود را بفرستید."
        )
        return reply, product, False

    if contains_any(normalized, ("محصول", "موجود", "چی دارید", "چه دارید", "لیست")):
        managed, products = list_catalog_products(db, store_slug)
        if not products:
            return "فعلاً محصول موجودی برای معرفی ثبت نشده است.", None, False
        names = "، ".join(product.name for product in products)
        label = "محصولات ما" if managed else "محصولات آزمایشی ما"
        return f"{label}: {names}. نام هرکدام را بفرستید تا قیمت را اعلام کنم.", None, False

    if contains_any(normalized, ("سلام", "درود", "وقت بخیر", "صبح بخیر", "شب بخیر")):
        return (
            "سلام! فارسی یا فینگلیش درباره قیمت، موجودی، ارسال، گارانتی یا ثبت سفارش سؤال کنید. "
            "هر زمان خواستید می‌توانید اپراتور را هم صدا بزنید.",
            None,
            False,
        )

    return (
        "هنوز پاسخ دقیقی برای این جمله ندارم. فارسی یا فینگلیش می‌توانید درباره محصول، قیمت، موجودی، تخفیف، ارسال، پرداخت، "
        "گارانتی، مرجوعی، رجیستری، ثبت سفارش یا ارتباط با اپراتور سؤال کنید."
    ), None, False


def process_chat(
    db: Session,
    payload: ChatRequest,
    channel: str = "web",
    *,
    commit: bool = True,
    store_slug: str = "default",
) -> dict:
    customer = db.scalar(
        select(Customer).where(Customer.instagram_user_id == payload.instagram_user_id)
    )
    if customer is None:
        customer = Customer(
            instagram_user_id=payload.instagram_user_id,
            name=payload.customer_name,
        )
        db.add(customer)
        db.flush()
    elif payload.customer_name and not customer.name:
        customer.name = payload.customer_name

    phone = extract_phone(payload.message)
    if phone:
        customer.phone = phone

    order = None
    if is_order_intent(payload.message):
        reply, product, needs_human, order = handle_order(
            db, customer, payload.message, store_slug
        )
    elif phone:
        reply = (
            "شماره شما با موفقیت ثبت شد. حالا می‌توانید بنویسید «سفارشم را ثبت کن» "
            "یا دکمه ارتباط با اپراتور را بزنید."
        )
        product = None
        needs_human = True
    else:
        reply, product, needs_human = build_reply(
            db, customer, payload.message, store_slug
        )

    conversation = Conversation(
        customer_id=customer.id,
        channel=channel,
        user_message=payload.message,
        assistant_message=reply,
        needs_human=needs_human,
    )
    db.add(conversation)
    if commit:
        db.commit()
    else:
        db.flush()

    return {
        "reply": reply,
        "customer_id": customer.id,
        "product": product,
        "order": order_to_dict(order) if order else None,
        "phone_saved": phone is not None,
        "needs_human": needs_human,
    }
