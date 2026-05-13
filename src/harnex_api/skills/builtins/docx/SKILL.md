# Word Document Builder (docx)

Produces a `.docx` Word document the user can download. Implementation runs in
the Harnex Blaxel sandbox under Node.js using the `docx` package (already
installed in the sandbox image).

## When to use

The user wants a Word document, formal letter, report, memo, structured
write-up — anything that should open in Microsoft Word / Google Docs / Pages.

## Output contract

Write the generated file to `${HARNEX_OUTPUT_DIR}/output.docx`. The runner
captures whatever lands in that directory and ships it to Azure Blob storage.
Do **not** print the binary to stdout; do not write to stdin/stdout other than
short progress messages.

## Authoring template

```js
const { Document, Packer, Paragraph, HeadingLevel, TextRun } = require("docx");
const fs = require("fs");
const path = require("path");

const doc = new Document({
  sections: [
    {
      properties: {},
      children: [
        new Paragraph({
          text: "Quarterly Report",
          heading: HeadingLevel.HEADING_1,
        }),
        new Paragraph({
          children: [
            new TextRun("Revenue grew "),
            new TextRun({ text: "23%", bold: true }),
            new TextRun(" quarter over quarter."),
          ],
        }),
      ],
    },
  ],
});

(async () => {
  const buffer = await Packer.toBuffer(doc);
  const outDir = process.env.HARNEX_OUTPUT_DIR;
  fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(path.join(outDir, "output.docx"), buffer);
})();
```

## Guidance

- Use `HeadingLevel.HEADING_1`/`HEADING_2`/`HEADING_3` rather than bold large
  text — readers using assistive tech rely on real headings.
- For tables use `Table` + `TableRow` + `TableCell` from the same package.
- For bullet/numbered lists pass `{ bullet: { level: 0 } }` or
  `{ numbering: { reference: "...", level: 0 } }` to `Paragraph`.
- Keep file size under 25 MB (runner caps reads at that).
