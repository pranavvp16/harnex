# Excel Spreadsheet Builder (xlsx)

Produces an `.xlsx` Excel workbook the user can download. Runs in the Harnex
Blaxel sandbox under Python using `openpyxl` (already installed).

## When to use

The user wants a spreadsheet — tabular data export, multi-sheet workbook,
analysis with formulas, or anything they'd open in Excel / Google Sheets /
Numbers.

## Output contract

Write the workbook to `${HARNEX_OUTPUT_DIR}/output.xlsx`. The runner captures
whatever lands in that directory and ships it to Azure Blob storage.

## Authoring template

```python
import os
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font

wb = Workbook()
ws = wb.active
ws.title = "Summary"
ws.append(["Region", "Revenue", "Growth"])
for cell in ws[1]:
    cell.font = Font(bold=True)
ws.append(["NA", 3_400_000, 0.23])
ws.append(["EU", 1_800_000, 0.17])
ws["D1"] = "Total"
ws["D2"] = "=SUM(B2:B3)"

out_dir = Path(os.environ["HARNEX_OUTPUT_DIR"])
out_dir.mkdir(parents=True, exist_ok=True)
wb.save(out_dir / "output.xlsx")
```

## Guidance

- Use `ws.append([...])` for rows; `ws.cell(row, column, value)` for sparse writes.
- Formulas are plain strings starting with `=`.
- For charts: `from openpyxl.chart import BarChart, Reference`.
- For multiple sheets: `wb.create_sheet(title="Q1")`.
- Keep file size under 25 MB.
