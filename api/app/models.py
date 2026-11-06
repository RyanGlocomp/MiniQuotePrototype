"""Data contracts between stages (design doc: Interface contracts).

- Extracted*: what the LLM returns (stage c). Every value may be null; nothing is guessed.
- Reviewed*:  what the human confirmed (screen 3). Pricing only accepts this.
"""
from decimal import Decimal

from pydantic import BaseModel, Field


# ---- stage c output: extracted.json -------------------------------------------------

class ExtractedValue(BaseModel):
    value: str | None = None
    confidence: float = Field(0.0, ge=0, le=1)
    source: str | None = None


class ExtractedHeader(BaseModel):
    partner: ExtractedValue = ExtractedValue()
    attention: ExtractedValue = ExtractedValue()
    project: ExtractedValue = ExtractedValue()
    quote_ref: ExtractedValue = ExtractedValue()


class ExtractedLineItem(BaseModel):
    part_no: str | None = None
    description: str | None = None
    qty: int | None = None
    unit_cost: Decimal | None = None  # unknown stays None, never 0
    confidence: float = Field(0.0, ge=0, le=1)
    source: str | None = None


class Flag(BaseModel):
    field: str
    reason: str  # "missing" | "low_confidence" | ...


class Extracted(BaseModel):
    job_id: str
    client: str
    brand: str
    model: dict[str, str] = {}
    header: ExtractedHeader = ExtractedHeader()
    line_items: list[ExtractedLineItem] = []
    flags: list[Flag] = []


# ---- after human review: reviewed.json ----------------------------------------------

class ReviewedHeader(BaseModel):
    partner: str | None = None
    attention: str | None = None
    project: str | None = None
    quote_ref: str | None = None


class ReviewedLineItem(BaseModel):
    part_no: str | None = None
    description: str | None = None
    qty: int | None = Field(None, ge=1)
    unit_cost: Decimal | None = Field(None, ge=0)


class Reviewed(BaseModel):
    client: str
    brand: str
    header: ReviewedHeader
    line_items: list[ReviewedLineItem]


# ---- stage d output -----------------------------------------------------------------

class PricedLine(BaseModel):
    part_no: str | None
    description: str | None
    qty: int
    unit_cost: Decimal
    unit_price: Decimal
    line_total: Decimal


class Totals(BaseModel):
    line_count: int
    unit_count: int
    subtotal: Decimal
    tax_rate: Decimal
    tax: Decimal
    total: Decimal


class Priced(BaseModel):
    header: ReviewedHeader
    lines: list[PricedLine]
    totals: Totals
    markup: Decimal
    pricing_hash: str
