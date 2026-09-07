from types import SimpleNamespace

import pytest

from app.automation_rules.runtime import normalize_match_text, rule_matches


@pytest.mark.parametrize(
    ("left", "right"),
    (
        ("قیمت محصول", "قيمت محصول"),
        ("کالا", "كالا"),
        ("نیم‌فاصله", "نیم فاصله"),
        ("  قیمت   محصول  ", "قیمت محصول"),
        ("\tقیمت\n", "قیمت"),
        ("DIRECTPILOT", "directpilot"),
        ("ＡＢＣ", "abc"),
        ("قیمت؟", "قیمت?"),
    ),
)
def test_match_normalization_is_deterministic(left, right):
    assert normalize_match_text(left) == normalize_match_text(right)


@pytest.mark.parametrize(
    ("match_type", "message", "keywords", "expected"),
    (
        ("EXACT", "  قيمت  ", ["قیمت"], True),
        ("EXACT", "قیمت محصول", ["قیمت"], False),
        ("CONTAINS", "لطفاً قیمت محصول را بگویید", ["قیمت"], True),
        ("STARTS_WITH", "قیمت محصول چقدر است", ["قیمت محصول"], True),
        ("STARTS_WITH", "لطفاً قیمت", ["قیمت"], False),
        ("CONTAINS", "ارسال دارید", ["قیمت", "ارسال"], True),
    ),
)
def test_rule_matching_contract(match_type, message, keywords, expected):
    rule = SimpleNamespace(match_type=match_type, keywords=keywords)
    assert rule_matches(rule, message) is expected
