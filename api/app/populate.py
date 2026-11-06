"""Stage e: fill the client template. Writes only the cells named in the field mapping."""
from pathlib import Path

from openpyxl import load_workbook

from .models import Priced
from .registry import Template


class PopulateError(ValueError):
    pass


def populate(priced: Priced, template: Template, out_path: Path) -> Path:
    m = template.mapping
    items = m["line_items"]
    if len(priced.lines) > items["max_rows"]:
        raise PopulateError(
            f"{len(priced.lines)} line items, template holds {items['max_rows']}")

    wb = load_workbook(template.file)  # keeps formulas; never runs macros
    ws = wb[m["sheet"]]

    for field, cell in m["header"].items():
        ws[cell] = getattr(priced.header, field)  # None leaves the cell blank

    ws[m["inputs"]["tax_rate"]] = priced.totals.tax_rate

    cols = items["columns"]
    for i, line in enumerate(priced.lines):
        row = items["first_row"] + i
        ws[f"{cols['part_no']}{row}"] = line.part_no
        ws[f"{cols['description']}{row}"] = line.description
        ws[f"{cols['qty']}{row}"] = line.qty
        ws[f"{cols['unit_price']}{row}"] = line.unit_price

    out_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out_path)
    return out_path
