# PowerPoint Presentation Builder (pptx)

Produces a `.pptx` slide deck the user can download. Runs in the Harnex Blaxel
sandbox under Python using `python-pptx` (already installed).

## When to use

The user wants a presentation, slide deck, or PowerPoint file — anything they
would present in a meeting or share as slides.

## Output contract

Write the deck to `${HARNEX_OUTPUT_DIR}/output.pptx`. The runner captures
whatever lands in that directory and ships it to Azure Blob storage.

## Authoring template

```python
import os
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt

prs = Presentation()

# Title slide
title_slide = prs.slides.add_slide(prs.slide_layouts[0])
title_slide.shapes.title.text = "Quarterly Review"
title_slide.placeholders[1].text = "Q1 2026"

# Bullet content slide
content_slide = prs.slides.add_slide(prs.slide_layouts[1])
content_slide.shapes.title.text = "Highlights"
body = content_slide.placeholders[1].text_frame
body.text = "Revenue grew 23% QoQ"
body.add_paragraph().text = "Three enterprise customers signed"
body.add_paragraph().text = "Churn down to 1.4%"

out_dir = Path(os.environ["HARNEX_OUTPUT_DIR"])
out_dir.mkdir(parents=True, exist_ok=True)
prs.save(out_dir / "output.pptx")
```

## Guidance

- Layouts: `prs.slide_layouts[0]` is the title slide; `[1]` is title +
  content; `[5]` is title only. Different templates vary.
- For tables: `slide.shapes.add_table(rows, cols, left, top, width, height)`.
- For images: `slide.shapes.add_picture(path, left, top, width, height)`.
- Use `Inches(1)` / `Pt(18)` for measurements.
- Keep file size under 25 MB.
