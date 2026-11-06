"""Stage d: deterministic pricing. Expected numbers are worked out by hand.

Rules (mini build placeholders): unit_price = cost x (1 + markup), rounded UP to RM0.10;
line_total = unit_price x qty; tax = round(subtotal x tax_rate, 2) half-up; total = subtotal + tax.
"""
from decimal import Decimal as D

import pytest

from app.models import Reviewed
from app.pricing import PricingError, price, round_up_10sen

RULES = dict(markup=D("0.20"), tax_rate=D("0.08"))


def reviewed(**over):
    data = {
        "client": "Demo Client",
        "brand": "Demo Brand",
        "header": {"partner": "ACME Sdn Bhd", "attention": "Aisha", "project": "DC refresh", "quote_ref": "Q-001"},
        "line_items": [
            {"part_no": "SW-48", "description": "48-port switch", "qty": 4, "unit_cost": "1234.56"},
            {"part_no": "SFP-10G", "description": "10G optic", "qty": 2, "unit_cost": "99.99"},
            {"part_no": "CAB-3M", "description": "3m patch cable", "qty": 3, "unit_cost": "10.00"},
        ],
    }
    data.update(over)
    return Reviewed.model_validate(data)


@pytest.mark.parametrize("raw, expected", [
    ("1481.472", "1481.50"),   # rounds up, not to nearest
    ("119.988", "120.00"),
    ("12.00", "12.00"),        # already on a 10-sen step: unchanged
    ("12.01", "12.10"),        # any fraction of 10 sen goes up
    ("0.001", "0.10"),
    ("0", "0.00"),
])
def test_round_up_10sen(raw, expected):
    assert round_up_10sen(D(raw)) == D(expected)


def test_price_hand_checked_totals():
    p = price(reviewed(), **RULES)
    assert [l.unit_price for l in p.lines] == [D("1481.50"), D("120.00"), D("12.00")]
    assert [l.line_total for l in p.lines] == [D("5926.00"), D("240.00"), D("36.00")]
    t = p.totals
    assert (t.line_count, t.unit_count) == (3, 9)
    assert t.subtotal == D("6202.00")
    assert t.tax == D("496.16")
    assert t.total == D("6698.16")


def test_tax_rounds_half_up():
    # subtotal 0.50 x 0.01 = 0.005 -> 0.01 (half-up, not banker's 0.00)
    r = reviewed(line_items=[{"part_no": "X", "description": "x", "qty": 1, "unit_cost": "0.40"}])
    p = price(r, markup=D("0.20"), tax_rate=D("0.01"))  # 0.48 -> 0.50
    assert p.totals.subtotal == D("0.50")
    assert p.totals.tax == D("0.01")


def test_missing_values_refuse_to_price():
    r = reviewed(line_items=[
        {"part_no": "SW-48", "description": "48-port switch", "qty": 4, "unit_cost": None},
        {"part_no": "SFP-10G", "description": "10G optic", "qty": None, "unit_cost": "99.99"},
    ])
    with pytest.raises(PricingError) as err:
        price(r, **RULES)
    assert err.value.fields == ["line_items[0].unit_cost", "line_items[1].qty"]


def test_no_line_items_refuses():
    with pytest.raises(PricingError):
        price(reviewed(line_items=[]), **RULES)


def test_hash_is_stable_and_changes_on_any_edit():
    a = price(reviewed(), **RULES).pricing_hash
    assert a == price(reviewed(), **RULES).pricing_hash
    edited = reviewed(header={"partner": "ACME Sdn Bhd", "attention": "Aisha",
                              "project": "DC refresh", "quote_ref": "Q-002"})
    assert price(edited, **RULES).pricing_hash != a
    assert price(reviewed(), markup=D("0.25"), tax_rate=D("0.08")).pricing_hash != a
