"""Builds quote_template.xlsx for the fake "Demo Client / Demo Brand".

The template holds formulas (line totals, subtotal, tax, total) the way a real client
template would. Stage e only writes input cells; stage f recalculates with LibreOffice and
reads the formula results back to check them against stage d.

Run:  uv run --project api python templates/demo_client/make_template.py
"""
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

OUT = Path(__file__).with_name("quote_template.xlsx")
FIRST_ROW, LAST_ROW = 12, 31  # 20 line-item rows

wb = Workbook()
ws = wb.active
ws.title = "Quote"

bold = Font(bold=True)
head_fill = PatternFill("solid", fgColor="0F5E59")
head_font = Font(bold=True, color="FFFFFF")
thin = Side(style="thin", color="BBBBBB")
box = Border(top=thin, bottom=thin, left=thin, right=thin)
money = '#,##0.00'

ws["A1"] = "QUOTATION"
ws["A1"].font = Font(bold=True, size=16)
ws["A2"] = "Demo Client · Demo Brand"

for row, label in [(4, "Partner"), (5, "Attention"), (6, "Project"), (7, "Quote ref")]:
    ws.cell(row=row, column=1, value=label).font = bold
ws["D9"] = "Tax rate"
ws["D9"].font = bold
ws["E9"].number_format = "0.00%"

headers = ["No.", "Part no.", "Description", "Qty", "Unit price (RM)", "Total (RM)"]
for col, text in enumerate(headers, start=1):
    c = ws.cell(row=FIRST_ROW - 1, column=col, value=text)
    c.font, c.fill, c.border = head_font, head_fill, box
    c.alignment = Alignment(horizontal="center")

for r in range(FIRST_ROW, LAST_ROW + 1):
    ws.cell(row=r, column=1, value=f'=IF(B{r}="","",ROW()-{FIRST_ROW - 1})')
    ws.cell(row=r, column=6, value=f'=IF(D{r}="","",D{r}*E{r})')
    ws.cell(row=r, column=5).number_format = money
    ws.cell(row=r, column=6).number_format = money
    for col in range(1, 7):
        ws.cell(row=r, column=col).border = box

t = LAST_ROW + 2
rows = [
    ("Line items", f'=COUNTA(B{FIRST_ROW}:B{LAST_ROW})', "0"),
    ("Units", f'=SUM(D{FIRST_ROW}:D{LAST_ROW})', "0"),
    ("Subtotal", f'=ROUND(SUM(F{FIRST_ROW}:F{LAST_ROW}),2)', money),
    ("Tax", f'=ROUND(F{t + 2}*E9,2)', money),
    ("Total", f'=F{t + 2}+F{t + 3}', money),
]
for i, (label, formula, fmt) in enumerate(rows):
    ws.cell(row=t + i, column=5, value=label).font = bold
    c = ws.cell(row=t + i, column=6, value=formula)
    c.number_format = fmt
    c.font = bold

for col, width in zip("ABCDEF", [6, 16, 40, 8, 16, 16]):
    ws.column_dimensions[col].width = width

wb.save(OUT)
print(f"wrote {OUT}  (line rows {FIRST_ROW}-{LAST_ROW}, totals F{t}-F{t + 4})")
