import pytest

from app.business_knowledge.industry import (
    COMMON_FIELDS,
    CUSTOMER_PROVENANCE,
    INDUSTRY_SCHEMAS,
    get_industry_schema,
    normalize_industry_attributes,
    serialize_industry_profile,
    fields_for_subcategory,
    industry_readiness,
)


def test_taxonomy_exposes_common_fields_and_industry_subcategories() -> None:
    assert len(COMMON_FIELDS) >= 10
    assert {"retail", "fashion", "restaurant", "insurance", "real_estate", "other"} <= set(INDUSTRY_SCHEMAS)
    assert get_industry_schema("FASHION").subcategories == ("apparel", "shoes", "accessories")


def test_industry_answers_are_normalized_without_inventing_values() -> None:
    attributes = normalize_industry_attributes(
        "fashion",
        {"sizes": "S، M, L", "colors": ["مشکی", " سفید ", ""], "fabric": "  لینن  "},
    )
    assert attributes == {"sizes": ["S", "M", "L"], "colors": ["مشکی", "سفید"], "fabric": "لینن"}


def test_industry_profile_serialization_is_versioned_and_customer_sourced() -> None:
    payload = serialize_industry_profile(
        industry_code="restaurant",
        subcategory="cafe",
        attributes={"menu_categories": "قهوه, دسر"},
    )
    assert payload["schema_version"] == 2
    assert payload["provenance"] == CUSTOMER_PROVENANCE
    assert payload["industry_code"] == "restaurant"
    assert payload["attributes"] == {"menu_categories": "قهوه, دسر"}


def test_industry_profile_rejects_unknown_fields_and_subcategories() -> None:
    with pytest.raises(ValueError, match="unknown industry field"):
        normalize_industry_attributes("retail", {"invented": "value"})
    with pytest.raises(ValueError, match="subcategory"):
        serialize_industry_profile(
            industry_code="retail", subcategory="clinic", attributes={}
        )


def test_all_industries_expose_readiness_and_valid_subcategory() -> None:
    assert len(INDUSTRY_SCHEMAS) == 16
    for code, schema in INDUSTRY_SCHEMAS.items():
        assert schema.subcategories
        subcategory = schema.subcategories[0]
        readiness = industry_readiness(code, {})
        assert readiness.completion_percent == 0 or not readiness.required_minimum
        assert set(schema.required_minimum) <= {field.key for field in schema.fields}
        visible = fields_for_subcategory(code, subcategory)
        assert {field.key for field in visible} >= {field.key for field in COMMON_FIELDS}


def test_subcategory_visibility_excludes_irrelevant_fields() -> None:
    apparel = {field.key for field in fields_for_subcategory("fashion", "apparel")}
    shoes = {field.key for field in fields_for_subcategory("fashion", "shoes")}
    assert "clothing_type" in apparel
    assert "clothing_type" not in shoes
    restaurant = {field.key for field in fields_for_subcategory("restaurant", "restaurant")}
    catering = {field.key for field in fields_for_subcategory("restaurant", "catering")}
    assert "reservation_method" in restaurant
    assert "reservation_method" not in catering
    insurance = {field.key for field in fields_for_subcategory("insurance", "insurance")}
    financial = {field.key for field in fields_for_subcategory("insurance", "financial_services")}
    assert "claim_process" in insurance
    assert "claim_process" not in financial


def test_readiness_ignores_minimum_fields_hidden_by_subcategory() -> None:
    shoes = industry_readiness("fashion", {}, "shoes")
    assert "clothing_type" not in shoes.required_minimum
    assert "clothing_type" not in shoes.missing_required
    assert shoes.completion_percent == 0
    partial = industry_readiness("fashion", {"sizes": "S"}, "shoes")
    assert partial.completion_percent == 25


def test_mixed_business_type_is_preserved_for_contextual_schemas() -> None:
    for code, subcategory in (("restaurant", "cafe"), ("automotive", "sales")):
        payload = serialize_industry_profile(
            industry_code=code,
            subcategory=subcategory,
            business_type="physical",
            attributes={},
        )
        assert payload["business_type"] == "physical"


def test_each_industry_accepts_only_its_subcategories_and_preserves_provenance() -> None:
    for code, schema in INDUSTRY_SCHEMAS.items():
        valid_subcategory = schema.subcategories[0]
        field = schema.fields[-1]
        value = (
            ["one", "two"]
            if field.value_type == "list"
            else field.options[0]
            if field.options
            else "provided"
        )
        payload = serialize_industry_profile(
            industry_code=code,
            subcategory=valid_subcategory,
            attributes={field.key: value, schema.fields[0].key: ""},
        )
        assert payload["provenance"] == CUSTOMER_PROVENANCE
        assert payload["subcategory"] == valid_subcategory
        assert field.key in payload["attributes"]
        assert schema.fields[0].key not in payload["attributes"]
        with pytest.raises(ValueError, match="subcategory"):
            serialize_industry_profile(
                industry_code=code,
                subcategory="not-a-valid-subcategory",
                attributes={},
            )


def test_commercial_option_fields_and_missing_values_are_safe() -> None:
    normalized = normalize_industry_attributes(
        "retail", {"price_type": "quote_required", "availability": "unknown", "refund_policy": ""}
    )
    assert normalized == {"price_type": "quote_required", "availability": "unknown"}
    with pytest.raises(ValueError, match="supported options"):
        normalize_industry_attributes("retail", {"availability": "maybe"})


def test_business_type_is_versioned_and_restricted() -> None:
    payload = serialize_industry_profile(
        industry_code="software",
        subcategory="saas",
        business_type="digital",
        attributes={"features": "گزارش"},
    )
    assert payload["business_type"] == "digital"
    with pytest.raises(ValueError, match="business type"):
        serialize_industry_profile(
            industry_code="software",
            subcategory="saas",
            business_type="service",
            attributes={},
        )
    mixed = serialize_industry_profile(
        industry_code="restaurant",
        subcategory="catering",
        business_type="service",
        attributes={"menu_categories": "پذیرایی"},
    )
    assert mixed["business_type"] == "service"
