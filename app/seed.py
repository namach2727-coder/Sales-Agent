from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import FAQ, Product


DEMO_PRODUCTS = [
    {
        "name": "Apple iPhone 15 128GB",
        "description": "موبایل آیفون ۱۵ با حافظه ۱۲۸ گیگابایت، رنگ مشکی، موجودی فرضی برای دمو",
        "price": 72_500_000,
        "is_available": True,
    },
    {
        "name": "Samsung Galaxy A55 256GB",
        "description": "موبایل اندرویدی سامسونگ با حافظه ۲۵۶ گیگابایت، رنگ سرمه‌ای، موجودی فرضی برای دمو",
        "price": 28_900_000,
        "is_available": True,
    },
    {
        "name": "قاب سیلیکونی iPhone 15",
        "description": "قاب سیلیکونی آیفون ۱۵، رنگ مشکی، موجودی فرضی برای دمو",
        "price": 850_000,
        "is_available": True,
    },
]

DEMO_FAQS = [
    {
        "question": "شرایط ارسال چیست؟",
        "answer": "ارسال آزمایشی برای تهران با پیک و برای سایر شهرها با پست انجام می‌شود.",
    },
    {
        "question": "آیا محصولات گارانتی دارند؟",
        "answer": "موبایل‌ها در این دمو با گارانتی فرضی ۱۸ ماهه و قاب با ضمانت سلامت تحویل در نظر گرفته شده‌اند.",
    },
    {
        "question": "روش پرداخت چگونه است؟",
        "answer": "در نسخه آزمایشی، پرداخت آنلاین فعال نیست و سفارش برای پیگیری اپراتور ثبت می‌شود.",
    },
    {
        "question": "شرایط مرجوعی چیست؟",
        "answer": "در این دمو، درخواست مرجوعی تا ۷ روز و فقط پس از بررسی سلامت کالا توسط اپراتور پذیرفته می‌شود.",
    },
    {
        "question": "آیا امکان خرید اقساطی وجود دارد؟",
        "answer": "خرید اقساطی در نسخه آزمایشی فعال نیست و شرایط واقعی باید توسط اپراتور تأیید شود.",
    },
    {
        "question": "آیا موبایل‌ها رجیستر شده‌اند؟",
        "answer": "موبایل‌های این دمو رجیسترشده و قابل انتقال در سامانه همتا در نظر گرفته شده‌اند.",
    },
]


def seed_demo_catalog(db: Session) -> None:
    existing_products = set(db.scalars(select(Product.name)).all())
    for data in DEMO_PRODUCTS:
        if data["name"] not in existing_products:
            db.add(Product(**data))

    existing_faqs = set(db.scalars(select(FAQ.question)).all())
    for data in DEMO_FAQS:
        if data["question"] not in existing_faqs:
            db.add(FAQ(**data))

    db.commit()
