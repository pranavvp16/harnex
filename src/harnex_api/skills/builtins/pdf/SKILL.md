# PDF Document Builder (pdf)

Produces a `.pdf` file the user can download. Runs in the Harnex Blaxel sandbox
under Python using ReportLab (`reportlab`, already installed).

## When to use

The user wants a PDF — a report, invoice, certificate, printable form, or any
document where layout fidelity across platforms matters.

## Output contract

Write the generated file to `${HARNEX_OUTPUT_DIR}/output.pdf`. The runner
captures whatever lands in that directory and ships it to Azure Blob storage.

## Authoring template

```python
import os
from pathlib import Path
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table

out_dir = Path(os.environ["HARNEX_OUTPUT_DIR"])
out_dir.mkdir(parents=True, exist_ok=True)
doc = SimpleDocTemplate(str(out_dir / "output.pdf"), pagesize=LETTER)
styles = getSampleStyleSheet()

story = [
    Paragraph("Quarterly Report", styles["Title"]),
    Spacer(1, 12),
    Paragraph("Revenue grew <b>23%</b> quarter over quarter.", styles["BodyText"]),
    Spacer(1, 12),
    Table([["Region", "Revenue"], ["NA", "$3.4M"], ["EU", "$1.8M"]]),
]

doc.build(story)
```

## Guidance

- Use Platypus flowables (`Paragraph`, `Table`, `Image`, `Spacer`, `PageBreak`)
  for content that should wrap and paginate naturally.
- For pixel-perfect layout (forms, certificates) drop down to `canvas.Canvas`.
- Keep file size under 25 MB.
- Embed images with `from reportlab.platypus import Image; Image("path.png",
  width=…, height=…)`.
