"""Stage d: pricing calculator. Plain Python with Decimal; never calls a model."""
import hashlib
import json
from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal

from .models import Priced, PricedLine, Reviewed, Totals

TEN_SEN = Decimal("0.10")
SEN = Decimal("0.01")


class PricingError(ValueError):
    """Raised when reviewed data still has gaps. Unknown values are never treated as 0."""

    def __init__(self, fields: list[str]):
        self.fields = fields
        super().__init__(f"cannot price, missing: {', '.join(fields)}")


def round_up_10sen(amount: Decimal) -> Decimal:
    """Round up to the next RM0.10 step; values already on a step are unchanged."""
    return (amount / TEN_SEN).to_integral_value(rounding=ROUND_CEILING) * TEN_SEN


def pricing_hash(reviewed: Reviewed, markup: Decimal, tax_rate: Decimal) -> str:
    """Fingerprint of everything that affects the output file. Approval is tied to it."""
    payload = {
        "reviewed": reviewed.model_dump(mode="json"),
        "markup": str(markup),
        "tax_rate": str(tax_rate),
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def price(reviewed: Reviewed, markup: Decimal, tax_rate: Decimal) -> Priced:
    missing = []
    if not reviewed.line_items:
        missing.append("line_items")
    for i, item in enumerate(reviewed.line_items):
        if item.qty is None:
            missing.append(f"line_items[{i}].qty")
        if item.unit_cost is None:
            missing.append(f"line_items[{i}].unit_cost")
    if missing:
        raise PricingError(sorted(missing))

    lines = []
    for item in reviewed.line_items:
        unit_price = round_up_10sen(item.unit_cost * (1 + markup))
        lines.append(PricedLine(
            part_no=item.part_no,
            description=item.description,
            qty=item.qty,
            unit_cost=item.unit_cost,
            unit_price=unit_price,
            line_total=(unit_price * item.qty).quantize(SEN),
        ))

    subtotal = sum((l.line_total for l in lines), Decimal("0")).quantize(SEN)
    tax = (subtotal * tax_rate).quantize(SEN, rounding=ROUND_HALF_UP)
    totals = Totals(
        line_count=len(lines),
        unit_count=sum(l.qty for l in lines),
        subtotal=subtotal,
        tax_rate=tax_rate,
        tax=tax,
        total=subtotal + tax,
    )
    return Priced(
        header=reviewed.header,
        lines=lines,
        totals=totals,
        markup=markup,
        pricing_hash=pricing_hash(reviewed, markup, tax_rate),
    )
