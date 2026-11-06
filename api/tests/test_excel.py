"""Stages e + f: populate the template, recalc with LibreOffice, read totals back (M1 golden test)."""
import json
from decimal import Decimal as D

import pytest
from openpyxl import load_workbook

from app.models import Reviewed
from app.populate import PopulateError, populate
from app.pricing import price
from app.recalc import TotalsMismatch, check, recalc
from app.registry import TemplateNotFound, get_template

RULES = dict(markup=D("0.20"), tax_rate=D("0.08"))


@pytest.fixture
def sample(root):
    data = json.loads((root / "samples" / "reviewed_demo.json").read_text())
    expected = data.pop("_expected_totals_markup_0.20_tax_0.08")
    return Reviewed.model_validate(data), expected


@pytest.fixture
def template(root):
    return get_template("Demo Client", "Demo Brand", root / "templates")


def test_unknown_template(root):
    with pytest.raises(TemplateNotFound):
        get_template("Nobody", "Nothing", root / "templates")


def test_populate_writes_only_mapped_cells(sample, template, tmp_path):
    reviewed, _ = sample
    out = populate(price(reviewed, **RULES), template, tmp_path / "output.xlsx")
    ws = load_workbook(out)["Quote"]
    assert ws["B4"].value == "ACME Sdn Bhd"
    assert ws["B7"].value == "Q-2026-001"
    assert [ws[f"B{r}"].value for r in (12, 13, 14, 15)] == ["SW-48", "SFP-10G", "CAB-3M", None]
    assert D(str(ws["E12"].value)) == D("1481.50")
    assert ws["F12"].value == "=IF(D12=\"\",\"\",D12*E12)"  # formula left intact
    assert ws["F35"].value.startswith("=ROUND(SUM(")


def test_populate_rejects_too_many_lines(sample, template, tmp_path):
    reviewed, _ = sample
    reviewed.line_items = reviewed.line_items * 7  # 21 rows > 20
    with pytest.raises(PopulateError):
        populate(price(reviewed, **RULES), template, tmp_path / "output.xlsx")


@pytest.mark.libreoffice
def test_golden_readback_matches_approved_totals(sample, template, tmp_path):
    reviewed, expected = sample
    priced = price(reviewed, **RULES)
    out = recalc(populate(priced, template, tmp_path / "output.xlsx"))
    got = check(out, template, priced.totals)
    assert got["line_count"] == expected["line_count"]
    assert got["unit_count"] == expected["unit_count"]
    for k in ("subtotal", "tax", "total"):
        assert got[k].quantize(D("0.01")) == D(expected[k])


@pytest.mark.libreoffice
def test_check_catches_a_tampered_file(sample, template, tmp_path):
    reviewed, _ = sample
    priced = price(reviewed, **RULES)
    out = populate(priced, template, tmp_path / "output.xlsx")
    wb = load_workbook(out)
    wb["Quote"]["E13"] = 125  # someone changed a unit price after approval
    wb.save(out)
    with pytest.raises(TotalsMismatch) as err:
        check(recalc(out), template, priced.totals)
    assert "subtotal" in err.value.diffs and "total" in err.value.diffs
