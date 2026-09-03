"""Data-driven industry taxonomy and validation for business knowledge.

Industry-specific answers are stored as a normal, versioned
``BusinessKnowledgeEntry`` (``industry-profile``).  Keeping the taxonomy in
application code avoids a schema migration for every new industry while the
entry lifecycle and tenant isolation remain those of FOUNDATION-07.
"""

from __future__ import annotations

from dataclasses import dataclass, field as dataclass_field, replace
from typing import Mapping


INDUSTRY_PROFILE_SLUG = "industry-profile"
INDUSTRY_PROFILE_VERSION = 2
CUSTOMER_PROVENANCE = "CUSTOMER_PROVIDED"
SYSTEM_PROVENANCE = "SYSTEM_DERIVED"

INDUSTRY_SECTION_LABELS: dict[str, str] = {
    "identity": "هویت کسب‌وکار",
    "operations": "نحوه ارائه و زمان‌بندی",
    "sales": "فروش و سفارش",
    "product": "محصول یا خدمت",
    "policies": "قوانین و شرایط",
    "customer_service": "پشتیبانی و ارتباط با مشتری",
    "catalog": "کاتالوگ و فهرست ارائه",
    "safety": "ملاحظات ایمنی",
    "custom": "اطلاعات اختصاصی کسب‌وکار",
}


@dataclass(frozen=True, slots=True)
class IndustryField:
    key: str
    label: str
    section: str
    value_type: str = "text"
    required: bool = False
    options: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class IndustrySchema:
    code: str
    label: str
    subcategories: tuple[str, ...]
    fields: tuple[IndustryField, ...]
    subcategory_fields: Mapping[str, tuple[str, ...]] = dataclass_field(
        default_factory=dict
    )
    required_minimum: tuple[str, ...] = ()
    recommended: tuple[str, ...] = ()
    optional: tuple[str, ...] = ()
    business_type: str = "mixed"
    safety_rules: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class IndustryReadiness:
    required_minimum: tuple[str, ...]
    recommended: tuple[str, ...]
    optional: tuple[str, ...]
    missing_required: tuple[str, ...]
    completion_percent: int
    minimum_met: bool


COMMON_FIELDS: tuple[IndustryField, ...] = (
    IndustryField("brand_positioning", "جایگاه و مزیت برند", "identity"),
    IndustryField("target_customers", "مشتریان هدف", "identity"),
    IndustryField("service_area", "محدوده خدمت‌رسانی", "operations"),
    IndustryField("working_days", "روزهای کاری", "operations"),
    IndustryField("working_hours", "ساعات کاری", "operations"),
    IndustryField("order_process", "نحوه ثبت سفارش", "sales"),
    IndustryField("payment_methods", "روش‌های پرداخت", "sales"),
    IndustryField("delivery_policy", "روش و زمان ارسال/تحویل", "sales"),
    IndustryField("customer_tone", "لحن پاسخ‌گویی", "customer_service"),
    IndustryField("escalation_rules", "موارد ارجاع به انسان", "customer_service"),
    IndustryField("price", "قیمت یا بازه قیمت", "sales", "price"),
    IndustryField("currency", "واحد پول", "sales"),
    IndustryField(
        "price_type",
        "نوع قیمت",
        "sales",
        options=("fixed", "starting_from", "range", "quote_required"),
    ),
    IndustryField(
        "availability",
        "وضعیت دسترسی",
        "sales",
        options=("available", "unavailable", "preorder", "on_request", "unknown"),
    ),
    IndustryField("refund_policy", "قوانین بازپرداخت", "policies"),
    IndustryField("warranty_policy", "گارانتی/ضمانت", "policies"),
)


def _fields(*items: IndustryField) -> tuple[IndustryField, ...]:
    return COMMON_FIELDS + items


INDUSTRY_SCHEMAS: dict[str, IndustrySchema] = {
    "retail": IndustrySchema(
        "retail", "خرده‌فروشی و فروش آنلاین", ("general_retail", "online_retail"),
        _fields(IndustryField("product_range", "گروه‌های محصول", "catalog"),
                IndustryField("return_policy", "قوانین مرجوعی", "policies")),
    ),
    "fashion": IndustrySchema(
        "fashion", "مد و پوشاک", ("apparel", "shoes", "accessories"),
        _fields(IndustryField("audience", "جنسیت/مخاطب", "product"),
                IndustryField("clothing_type", "نوع پوشاک", "product"),
                IndustryField("sizes", "سایزها", "product", "list"),
                IndustryField("colors", "رنگ‌ها", "product", "list"),
                IndustryField("fabric", "جنس و پارچه", "product"),
                IndustryField("fit", "تن‌خور", "product"),
                IndustryField("season", "فصل مصرف", "product"),
                IndustryField("size_guide", "راهنمای سایز", "product"),
                IndustryField("exchange_policy", "قوانین تعویض سایز", "policies"),
                IndustryField("measurements", "اندازه‌ها و ابعاد", "product"),
                IndustryField("care_instructions", "روش نگهداری", "product"),
                IndustryField("refund_rules", "قوانین بازپرداخت", "policies"),
                IndustryField("recommendation_rules", "راهنمای پیشنهاد محصول", "customer_service"),
                IndustryField("variant_sku", "شناسه هر تنوع", "catalog"),
                IndustryField("variant_price", "قیمت هر تنوع", "sales", "price"),
                IndustryField("variant_stock", "موجودی هر تنوع", "catalog", "number")),
    ),
    "beauty": IndustrySchema(
        "beauty", "زیبایی و مراقبت شخصی", ("cosmetics", "skincare", "haircare"),
        _fields(IndustryField("skin_hair_type", "نوع پوست/مو", "product"),
                IndustryField("purpose", "کاربرد محصول", "product"),
                IndustryField("ingredients", "ترکیبات اعلام‌شده", "product"),
                IndustryField("usage", "روش مصرف", "product"),
                IndustryField("warnings", "هشدارهای اعلام‌شده", "safety"),
                IndustryField("authenticity", "اطلاعات اصالت", "product"),
                IndustryField("contraindications", "موارد منع مصرف اعلام‌شده", "safety"),
                IndustryField("expiry_batch", "تاریخ مصرف و شماره سری ساخت", "safety"),
                IndustryField("usage_restrictions", "محدودیت‌های مصرف", "safety"),
                IndustryField("patch_test_guidance", "راهنمای تست حساسیت", "safety"),
                IndustryField("recommendation_limits", "محدودیت‌های پیشنهاد محصول", "customer_service")),
    ),
    "restaurant": IndustrySchema(
        "restaurant", "رستوران، کافه و غذا", ("restaurant", "cafe", "catering"),
        _fields(IndustryField("menu_categories", "دسته‌بندی منو", "catalog"),
                IndustryField("ingredients", "مواد اولیه", "product"),
                IndustryField("serving_size", "اندازه سرو", "product"),
                IndustryField("preparation_time", "زمان آماده‌سازی", "operations"),
                IndustryField("dietary_options", "گزینه‌های گیاهی/رژیمی", "product"),
                IndustryField("allergens", "اطلاعات آلرژن", "safety"),
                IndustryField("fulfilment_modes", "حضوری/بیرون‌بر/ارسال", "sales"),
                IndustryField("delivery_zones", "محدوده‌های ارسال", "sales"),
                IndustryField("delivery_fee", "هزینه ارسال", "sales"),
                IndustryField("item_price", "قیمت هر آیتم منو", "sales", "price"),
                IndustryField("item_availability", "دسترسی هر آیتم", "sales", options=("available", "unavailable", "preorder", "on_request", "unknown")),
                IndustryField("customization", "امکان تغییر سفارش", "product"),
                IndustryField("reservation_method", "روش رزرو", "sales"),
                IndustryField("allergy_escalation", "موارد ارجاع درباره آلرژی", "safety")),
    ),
    "grocery": IndustrySchema(
        "grocery", "سوپرمارکت و کالاهای مصرفی", ("grocery", "fmcg"),
        _fields(IndustryField("brands", "برندها", "catalog"),
                IndustryField("pack_sizes", "اندازه بسته", "product"),
                IndustryField("storage", "شرایط نگهداری", "product"),
                IndustryField("expiry_policy", "سیاست تاریخ مصرف", "policies"),
                IndustryField("minimum_order", "حداقل سفارش", "sales"),
                IndustryField("sku_barcode", "شناسه یا بارکد", "catalog"),
                IndustryField("unit", "واحد فروش", "product"),
                IndustryField("substitutions", "قوانین جایگزینی کالا", "sales"),
                IndustryField("allergens", "آلرژن‌های اعلام‌شده", "safety")),
    ),
    "insurance": IndustrySchema(
        "insurance", "بیمه و خدمات مالی", ("insurance", "financial_services"),
        _fields(IndustryField("service_type", "نوع خدمت/بیمه", "product"),
                IndustryField("coverage", "پوشش‌های اعلام‌شده", "product"),
                IndustryField("exclusions", "استثناها", "policies"),
                IndustryField("eligibility", "شرایط دریافت", "sales"),
                IndustryField("required_documents", "مدارک لازم", "sales"),
                IndustryField("claim_process", "فرایند خسارت", "operations"),
                IndustryField("renewal", "تمدید و لغو", "policies"),
                IndustryField("quote_inputs", "اطلاعات لازم برای برآورد", "sales"),
                IndustryField("license_regulator", "مجوز یا نهاد ناظر", "safety"),
                IndustryField("human_review_rules", "موارد بررسی الزامی توسط کارشناس", "safety")),
    ),
    "real_estate": IndustrySchema(
        "real_estate", "املاک", ("sale", "rent", "property_management"),
        _fields(IndustryField("transaction_type", "فروش/اجاره", "product"),
                IndustryField("property_types", "نوع ملک", "product"),
                IndustryField("locations", "محدوده‌ها", "operations"),
                IndustryField("price_rules", "نحوه اعلام قیمت", "sales"),
                IndustryField("viewing_process", "فرایند بازدید", "operations"),
                IndustryField("listing_details", "جزئیات هر ملک", "product"),
                IndustryField("area", "متراژ", "product", "number"),
                IndustryField("bedrooms", "تعداد اتاق", "product", "number"),
                IndustryField("exact_location", "محدوده یا نشانی ملک", "operations"),
                IndustryField("deposit_rent", "ودیعه و اجاره", "sales"),
                IndustryField("amenities", "امکانات", "product"),
                IndustryField("appointment_availability", "زمان‌های بازدید", "operations")),
    ),
    "education": IndustrySchema(
        "education", "آموزش و دوره", ("courses", "tutoring", "academy"),
        _fields(IndustryField("subjects", "موضوعات آموزشی", "catalog"),
                IndustryField("levels", "سطح‌ها", "product"),
                IndustryField("prerequisites", "پیش‌نیازها", "product"),
                IndustryField("duration", "مدت دوره", "operations"),
                IndustryField("schedule", "برنامه برگزاری", "operations"),
                IndustryField("certificate", "گواهی", "product"),
                IndustryField("enrolment_process", "نحوه ثبت‌نام", "sales"),
                IndustryField("course_price", "هزینه دوره", "sales"),
                IndustryField("instructor", "مدرس", "product"),
                IndustryField("capacity", "ظرفیت", "operations"),
                IndustryField("start_date", "تاریخ شروع", "operations"),
                IndustryField("delivery_mode", "حضوری/آنلاین", "operations"),
                IndustryField("refund_cancellation", "قوانین بازپرداخت و لغو", "policies")),
    ),
    "health": IndustrySchema(
        "health", "سلامت و خدمات پزشکی", ("clinic", "medical", "wellness"),
        _fields(IndustryField("service_types", "نوع خدمات", "catalog"),
                IndustryField("specialty", "تخصص", "product"),
                IndustryField("appointment_methods", "روش نوبت‌دهی", "sales"),
                IndustryField("appointment_duration", "مدت نوبت", "operations"),
                IndustryField("preparation", "دستورهای آماده‌سازی", "operations"),
                IndustryField("accepted_insurance", "بیمه‌های پذیرفته‌شده", "sales"),
                IndustryField("provider_clinic", "نام پزشک یا مرکز", "identity"),
                IndustryField("location", "نشانی ارائه خدمت", "operations"),
                IndustryField("approved_price", "هزینه اعلام‌شده", "sales"),
                IndustryField("emergency_boundary", "مرز خدمات فوری", "safety"),
                IndustryField("human_escalation", "موارد ارجاع فوری به انسان", "safety")),
    ),
    "automotive": IndustrySchema(
        "automotive", "خودرو و خدمات خودرو", ("sales", "repair", "parts"),
        _fields(IndustryField("vehicle_types", "نوع خودرو", "product"),
                IndustryField("models", "مدل‌های پشتیبانی‌شده", "product"),
                IndustryField("service_types", "نوع خدمات", "catalog"),
                IndustryField("compatibility", "سازگاری قطعات", "product"),
                IndustryField("warranty", "گارانتی", "policies"),
                IndustryField("make_model_year", "برند، مدل و سال", "product"),
                IndustryField("part_sku", "شناسه قطعه", "catalog"),
                IndustryField("service_booking", "نوبت‌دهی خدمات", "sales"),
                IndustryField("service_availability", "زمان دسترسی خدمات", "operations")),
    ),
    "home_services": IndustrySchema(
        "home_services", "خدمات فنی و منزل", ("installation", "repair", "maintenance"),
        _fields(IndustryField("service_types", "نوع خدمات", "catalog"),
                IndustryField("supported_items", "دستگاه/ملک پشتیبانی‌شده", "product"),
                IndustryField("visit_fee", "هزینه بازدید", "sales"),
                IndustryField("emergency_service", "خدمات فوری", "operations"),
                IndustryField("service_warranty", "ضمانت خدمت", "policies"),
                IndustryField("response_time", "زمان پاسخ‌گویی", "operations"),
                IndustryField("booking", "روش رزرو خدمت", "sales"),
                IndustryField("technician_restrictions", "محدودیت‌های فنی یا ایمنی", "safety")),
    ),
    "professional_services": IndustrySchema(
        "professional_services", "خدمات حرفه‌ای", ("consulting", "legal", "accounting"),
        _fields(IndustryField("service_types", "نوع خدمات", "catalog"),
                IndustryField("specialty", "تخصص", "product"),
                IndustryField("deliverables", "خروجی خدمت", "product"),
                IndustryField("process", "فرایند همکاری", "operations"),
                IndustryField("pricing_model", "مدل قیمت‌گذاری", "sales"),
                IndustryField("scope_limits", "محدوده و استثناها", "policies"),
                IndustryField("credentials", "مجوز یا سابقه مرتبط", "identity"),
                IndustryField("duration", "مدت انجام خدمت", "operations"),
                IndustryField("jurisdiction", "حوزه و محدوده صلاحیت", "policies"),
                IndustryField("confidentiality", "انتظارات محرمانگی", "policies")),
    ),
    "travel": IndustrySchema(
        "travel", "سفر و اقامت", ("travel", "hotel", "tourism"),
        _fields(IndustryField("destinations", "مقصدها", "catalog"),
                IndustryField("booking_requirements", "شرایط رزرو", "sales"),
                IndustryField("included_services", "خدمات شامل", "product"),
                IndustryField("cancellation_rules", "قوانین لغو", "policies"),
                IndustryField("checkin_checkout", "ورود و خروج", "operations"),
                IndustryField("date_availability", "ظرفیت و دسترسی بر اساس تاریخ", "operations"),
                IndustryField("capacity", "ظرفیت", "operations"),
                IndustryField("excluded_services", "خدمات خارج از پکیج", "product")),
    ),
    "software": IndustrySchema(
        "software", "نرم‌افزار و محصولات دیجیتال", ("saas", "digital_product"),
        _fields(IndustryField("use_cases", "کاربردها", "product"),
                IndustryField("platforms", "پلتفرم‌ها", "product"),
                IndustryField("features", "ویژگی‌ها", "product"),
                IndustryField("limits", "محدودیت‌ها", "policies"),
                IndustryField("onboarding", "شروع استفاده", "operations"),
                IndustryField("trial", "دوره آزمایشی", "sales"),
                IndustryField("cancellation", "لغو", "policies"),
                IndustryField("plans", "پلن‌ها", "catalog"),
                IndustryField("integrations", "اتصال‌ها و یکپارچه‌سازی‌ها", "product"),
                IndustryField("billing", "صورتحساب", "sales"),
                IndustryField("support", "پشتیبانی", "customer_service"),
                IndustryField("security_privacy", "اطلاعات امنیت و حریم خصوصی اعلام‌شده", "safety")),
    ),
    "manufacturing": IndustrySchema(
        "manufacturing", "تولید، فروش و خدمات سازمانی (B2B)", ("manufacturing", "wholesale", "distribution"),
        _fields(IndustryField("product_families", "گروه محصول", "catalog"),
                IndustryField("specifications", "مشخصات فنی", "product"),
                IndustryField("minimum_order_quantity", "حداقل مقدار سفارش", "sales"),
                IndustryField("lead_time", "زمان آماده‌سازی", "operations"),
                IndustryField("delivery_terms", "شرایط تحویل", "sales"),
                IndustryField("customization", "سفارشی‌سازی", "product"),
                IndustryField("quote_process", "فرایند استعلام قیمت", "sales"),
                IndustryField("item_code", "کد کالا", "catalog"),
                IndustryField("unit_pack", "واحد و بسته‌بندی", "product"),
                IndustryField("capacity", "ظرفیت تولید", "operations"),
                IndustryField("certifications", "گواهی‌ها و استانداردهای اعلام‌شده", "safety"),
                IndustryField("credit_terms", "شرایط پرداخت و اعتبار", "sales")),
    ),
    "other": IndustrySchema(
        "other", "سایر", ("other",),
        _fields(
            IndustryField("business_specific_facts", "اطلاعات اختصاصی کسب‌وکار", "custom"),
            IndustryField("custom_text", "اطلاعات متنی اختصاصی", "custom"),
            IndustryField("custom_number", "عدد اختصاصی", "custom", "number"),
            IndustryField("custom_list", "فهرست اختصاصی", "custom", "list"),
            IndustryField("custom_price", "قیمت اختصاصی", "custom", "price"),
            IndustryField("custom_availability", "دسترسی اختصاصی", "custom", options=("available", "unavailable", "preorder", "on_request", "unknown")),
            IndustryField("custom_yes_no", "بله یا خیر", "custom", "boolean", options=("yes", "no")),
        ),
    ),
}


def _subcategory_fields(
    subcategories: tuple[str, ...], fields: tuple[str, ...]
) -> dict[str, tuple[str, ...]]:
    """Build an explicit, data-only visibility map for a schema."""

    return {subcategory: fields for subcategory in subcategories}


_INDUSTRY_METADATA: dict[str, dict[str, object]] = {
    "retail": {
        "business_type": "physical",
        "required_minimum": ("product_range", "order_process", "payment_methods", "delivery_policy"),
        "recommended": ("price_type", "availability", "refund_policy", "warranty_policy"),
        "optional": ("brand_positioning", "target_customers", "customer_tone"),
        "safety_rules": (),
    },
    "fashion": {
        "business_type": "physical",
        "subcategory_fields": {
            "apparel": ("audience", "clothing_type", "sizes", "colors", "fabric", "fit", "season", "size_guide", "measurements", "care_instructions", "exchange_policy", "refund_rules", "recommendation_rules", "variant_sku", "variant_price", "variant_stock"),
            "shoes": ("audience", "sizes", "colors", "fabric", "fit", "season", "size_guide", "measurements", "care_instructions", "exchange_policy", "refund_rules", "recommendation_rules", "variant_sku", "variant_price", "variant_stock"),
            "accessories": ("audience", "colors", "fabric", "season", "care_instructions", "exchange_policy", "refund_rules", "recommendation_rules", "variant_sku", "variant_price", "variant_stock"),
        },
        "required_minimum": ("clothing_type", "sizes", "order_process", "payment_methods", "delivery_policy"),
        "recommended": ("price", "currency", "colors", "measurements", "care_instructions", "exchange_policy", "recommendation_rules", "variant_sku", "variant_price", "variant_stock"),
        "optional": ("fabric", "fit", "season", "brand_positioning", "customer_tone"),
        "safety_rules": (),
    },
    "beauty": {
        "business_type": "physical",
        "required_minimum": ("purpose", "usage", "price_type", "availability", "payment_methods", "delivery_policy"),
        "recommended": ("skin_hair_type", "ingredients", "warnings", "contraindications", "expiry_batch", "patch_test_guidance", "recommendation_limits"),
        "optional": ("authenticity", "brand_positioning", "customer_tone"),
        "safety_rules": ("Only repeat customer-provided warnings and usage limits.", "Do not diagnose or promise a medical outcome."),
    },
    "restaurant": {
        "business_type": "mixed",
        "subcategory_fields": {
            "restaurant": ("menu_categories", "ingredients", "serving_size", "preparation_time", "dietary_options", "allergens", "fulfilment_modes", "delivery_zones", "delivery_fee", "item_price", "item_availability", "customization", "reservation_method", "allergy_escalation"),
            "cafe": ("menu_categories", "ingredients", "serving_size", "preparation_time", "dietary_options", "allergens", "fulfilment_modes", "delivery_zones", "delivery_fee", "item_price", "item_availability", "customization", "reservation_method", "allergy_escalation"),
            "catering": ("menu_categories", "ingredients", "serving_size", "preparation_time", "dietary_options", "allergens", "fulfilment_modes", "delivery_zones", "delivery_fee", "item_price", "item_availability", "customization", "allergy_escalation"),
        },
        "required_minimum": ("menu_categories", "fulfilment_modes", "payment_methods", "delivery_policy"),
        "recommended": ("price", "currency", "ingredients", "allergens", "delivery_zones", "delivery_fee", "item_price", "item_availability", "customization", "reservation_method"),
        "optional": ("serving_size", "preparation_time", "dietary_options", "customer_tone"),
        "safety_rules": ("Allergen information must be treated as customer-provided and incomplete unless explicitly stated.",),
    },
    "grocery": {
        "business_type": "physical",
        "required_minimum": ("brands", "pack_sizes", "payment_methods", "delivery_policy"),
        "recommended": ("sku_barcode", "unit", "availability", "substitutions", "storage", "expiry_policy", "allergens"),
        "optional": ("minimum_order", "customer_tone"),
        "safety_rules": ("Do not infer expiry, storage, nutrition, or allergen facts.",),
    },
    "insurance": {
        "business_type": "service",
        "subcategory_fields": {
            "insurance": ("service_type", "coverage", "exclusions", "eligibility", "required_documents", "claim_process", "renewal", "quote_inputs", "license_regulator", "human_review_rules"),
            "financial_services": ("service_type", "coverage", "exclusions", "eligibility", "required_documents", "renewal", "quote_inputs", "license_regulator", "human_review_rules"),
        },
        "required_minimum": ("service_type", "eligibility", "required_documents", "order_process", "escalation_rules"),
        "recommended": ("coverage", "exclusions", "quote_inputs", "license_regulator", "human_review_rules", "renewal"),
        "optional": ("claim_process", "customer_tone"),
        "safety_rules": ("Never guarantee coverage, approval, premium, or claim outcome.", "Escalate contract-specific questions to a human.",),
    },
    "real_estate": {
        "business_type": "service",
        "required_minimum": ("transaction_type", "property_types", "locations", "price_rules", "viewing_process"),
        "recommended": ("price", "currency", "listing_details", "area", "bedrooms", "exact_location", "deposit_rent", "amenities", "appointment_availability", "availability"),
        "optional": ("target_customers", "customer_tone"),
        "safety_rules": ("Do not invent listing, legal, financing, or availability facts.",),
    },
    "education": {
        "business_type": "service",
        "required_minimum": ("subjects", "levels", "schedule", "enrolment_process", "payment_methods"),
        "recommended": ("prerequisites", "duration", "course_price", "instructor", "capacity", "start_date", "delivery_mode", "refund_cancellation"),
        "optional": ("certificate", "customer_tone"),
        "safety_rules": (),
    },
    "health": {
        "business_type": "service",
        "required_minimum": ("service_types", "specialty", "appointment_methods", "location", "escalation_rules"),
        "recommended": ("provider_clinic", "appointment_duration", "preparation", "accepted_insurance", "approved_price", "emergency_boundary", "human_escalation"),
        "optional": ("customer_tone", "working_hours"),
        "safety_rules": ("Do not diagnose, prescribe, or reassure about emergencies.", "Escalate urgent or clinical questions to a qualified human.",),
    },
    "automotive": {
        "business_type": "mixed",
        "subcategory_fields": {
            "sales": ("vehicle_types", "models", "make_model_year", "warranty"),
            "repair": ("vehicle_types", "models", "service_types", "compatibility", "warranty", "make_model_year", "service_booking", "service_availability"),
            "parts": ("vehicle_types", "models", "compatibility", "warranty", "part_sku", "make_model_year"),
        },
        "required_minimum": ("vehicle_types", "service_types", "order_process", "payment_methods"),
        "recommended": ("models", "compatibility", "part_sku", "warranty", "service_booking", "service_availability"),
        "optional": ("make_model_year", "customer_tone"),
        "safety_rules": ("Do not provide safety-critical mechanical instructions beyond supplied information.",),
    },
    "home_services": {
        "business_type": "service",
        "required_minimum": ("service_types", "service_area", "order_process", "availability", "escalation_rules"),
        "recommended": ("visit_fee", "response_time", "booking", "service_warranty", "technician_restrictions", "emergency_service"),
        "optional": ("supported_items", "customer_tone"),
        "safety_rules": ("Do not provide hazardous-work instructions; escalate safety concerns.",),
    },
    "professional_services": {
        "business_type": "service",
        "required_minimum": ("service_types", "process", "pricing_model", "scope_limits", "escalation_rules"),
        "recommended": ("credentials", "duration", "availability", "jurisdiction", "confidentiality"),
        "optional": ("deliverables", "customer_tone"),
        "safety_rules": ("Do not present legal, tax, or accounting information as professional advice.",),
    },
    "travel": {
        "business_type": "service",
        "required_minimum": ("destinations", "booking_requirements", "cancellation_rules", "checkin_checkout", "payment_methods"),
        "recommended": ("date_availability", "capacity", "price", "included_services", "excluded_services"),
        "optional": ("service_area", "customer_tone"),
        "safety_rules": ("Do not infer availability, visa eligibility, or cancellation outcomes.",),
    },
    "software": {
        "business_type": "digital",
        "required_minimum": ("use_cases", "features", "limits", "trial", "cancellation"),
        "recommended": ("plans", "platforms", "integrations", "billing", "support", "security_privacy"),
        "optional": ("onboarding", "customer_tone"),
        "safety_rules": ("Only make security or privacy claims explicitly supplied by the customer.",),
    },
    "manufacturing": {
        "business_type": "physical",
        "required_minimum": ("product_families", "specifications", "minimum_order_quantity", "lead_time", "quote_process"),
        "recommended": ("item_code", "unit_pack", "capacity", "certifications", "delivery_terms", "credit_terms"),
        "optional": ("customization", "customer_tone"),
        "safety_rules": ("Do not infer certifications, capacity, or technical compliance.",),
    },
    "other": {
        "business_type": "mixed",
        "required_minimum": ("business_specific_facts", "order_process", "payment_methods", "escalation_rules"),
        "recommended": ("price", "currency", "price_type", "availability", "delivery_policy", "refund_policy", "warranty_policy"),
        "optional": ("brand_positioning", "target_customers", "customer_tone", "custom_text", "custom_number", "custom_list", "custom_price", "custom_availability", "custom_yes_no"),
        "safety_rules": ("Use only facts explicitly supplied by the business and escalate domain-sensitive questions.",),
    },
}


for _code, _metadata in _INDUSTRY_METADATA.items():
    INDUSTRY_SCHEMAS[_code] = replace(INDUSTRY_SCHEMAS[_code], **_metadata)


def fields_for_subcategory(
    industry_code: str, subcategory: str | None = None
) -> tuple[IndustryField, ...]:
    """Return common fields plus only fields relevant to a subcategory."""

    schema = get_industry_schema(industry_code)
    if schema is None:
        return ()
    visible = schema.subcategory_fields.get(subcategory or "")
    if not visible:
        return schema.fields
    keys = set(visible) | {field.key for field in COMMON_FIELDS}
    return tuple(field for field in schema.fields if field.key in keys)


def allowed_business_types(schema: IndustrySchema) -> frozenset[str]:
    """Return the presentation modes accepted by one industry schema."""

    allowed = {schema.business_type}
    if schema.business_type == "mixed":
        allowed.update({"physical", "digital", "service"})
    elif schema.business_type in {"physical", "service"}:
        # A store may legitimately offer a service alongside its primary
        # physical/service category without changing its industry taxonomy.
        allowed.add("mixed")
    return frozenset(allowed)


def industry_readiness(
    industry_code: str,
    attributes: Mapping[str, object],
    subcategory: str | None = None,
) -> IndustryReadiness:
    """Compute transparent readiness without making optional fields mandatory."""

    schema = get_industry_schema(industry_code)
    if schema is None:
        raise ValueError("unknown industry")
    supplied = {
        str(key) for key, value in attributes.items() if value not in (None, "", [])
    }
    visible_keys = {
        field.key for field in fields_for_subcategory(industry_code, subcategory)
    }
    required_minimum = tuple(
        key for key in schema.required_minimum if key in visible_keys
    )
    recommended = tuple(key for key in schema.recommended if key in visible_keys)
    optional = tuple(key for key in schema.optional if key in visible_keys)
    missing = tuple(key for key in required_minimum if key not in supplied)
    total = len(required_minimum)
    percent = 100 if not total else round((total - len(missing)) / total * 100)
    return IndustryReadiness(
        required_minimum=required_minimum,
        recommended=recommended,
        optional=optional,
        missing_required=missing,
        completion_percent=percent,
        minimum_met=not missing,
    )


def get_industry_schema(code: str) -> IndustrySchema | None:
    return INDUSTRY_SCHEMAS.get(code.strip().casefold())


def normalize_industry_attributes(
    industry_code: str,
    attributes: Mapping[str, object],
) -> dict[str, str | list[str]]:
    """Validate and normalize customer-provided answers for one schema."""

    schema = get_industry_schema(industry_code)
    if schema is None:
        raise ValueError("unknown industry")
    allowed = {field.key: field for field in schema.fields}
    normalized: dict[str, str | list[str]] = {}
    for key, value in attributes.items():
        field = allowed.get(str(key))
        if field is None:
            raise ValueError(f"unknown industry field: {key}")
        if field.value_type == "list":
            if isinstance(value, str):
                values = [part.strip() for part in value.replace("،", ",").split(",")]
            elif isinstance(value, (list, tuple)):
                values = [str(part).strip() for part in value if part is not None]
            else:
                if value is None:
                    continue
                raise ValueError(f"{key} must be a list")
            values = [part for part in values if part]
            if values:
                normalized[field.key] = values[:50]
            continue
        if value is None:
            continue
        if isinstance(value, (dict, set, bytes)):
            raise ValueError(f"{key} must be text")
        text = str(value).replace("\x00", "").strip()
        if text:
            if field.options and text not in field.options:
                raise ValueError(f"{key} must be one of the supported options")
            normalized[field.key] = text[:2_000]
    missing = [field.key for field in schema.fields if field.required and field.key not in normalized]
    if missing:
        raise ValueError("required industry fields are missing")
    return normalized


def serialize_industry_profile(
    *,
    industry_code: str,
    subcategory: str | None,
    attributes: Mapping[str, object],
    business_type: str | None = None,
) -> dict[str, object]:
    schema = get_industry_schema(industry_code)
    if schema is None:
        raise ValueError("unknown industry")
    normalized_subcategory = subcategory.strip() if isinstance(subcategory, str) else None
    if normalized_subcategory and normalized_subcategory not in schema.subcategories:
        raise ValueError("subcategory does not belong to industry")
    normalized_business_type = (business_type or schema.business_type).strip().casefold()
    if normalized_business_type not in allowed_business_types(schema):
        raise ValueError("business type is invalid")
    return {
        "schema_version": INDUSTRY_PROFILE_VERSION,
        "industry_code": schema.code,
        "subcategory": normalized_subcategory,
        "business_type": normalized_business_type,
        "attributes": normalize_industry_attributes(schema.code, attributes),
        "provenance": CUSTOMER_PROVENANCE,
    }
