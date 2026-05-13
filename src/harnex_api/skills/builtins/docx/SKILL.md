# Harnex sandbox contract — READ THIS FIRST

This skill is executed by the Harnex MCP `execute` tool inside an isolated
Blaxel sandbox. The runtime is fixed per skill (Python or Node.js) and the
working directory starts empty. There is no internet access from inside the
sandbox.

**Output contract.** Write your generated file(s) to
`${HARNEX_OUTPUT_DIR}/<filename>.<ext>`. The Harnex runner captures whatever
lands in that directory after your code finishes and uploads it to
tenant-isolated object storage; the `execute` response returns a short-lived
`download_url`.

**About the authoring notes below.** They come from Composio's
`awesome-claude-skills` collection (MIT licensed) and were written for an
interactive Claude environment with filesystem access to helper files. In
the Harnex sandbox those helper files **are not present on disk** — treat
references to sibling docs (e.g. `forms.md`, `ooxml.md`, helper scripts) as
advisory background. Use them as inspiration while writing your code; do
not try to `Read` them at runtime.

---

# Harnex: Node.js execution only

This built-in’s `execute` call runs **JavaScript** in an isolated **Node**
sandbox. The `docx` package is available via `require("docx")`. **Python,
pandoc, LibreOffice, Poppler, and other CLI tools mentioned later in this guide
are not installed** — those sections are retained from upstream as conceptual
reference on how `.docx` works, not as runnable steps inside Harnex.

**Creating a new `.docx`.** Use **docx-js** only. MCP `search(skills=true)`
returns this `SKILL.md` body as `instructions` only — there is no separate
`Read` step for `docx-js.md`. Use the **Minimal docx-js template (Harnex)**
below and extend it with the public `docx` npm API (`Paragraph`, `Table`,
`ImageRun`, …).

**Editing or redlining an existing `.docx`.** You cannot run the Python
Document library, `python ooxml/scripts/...`, or `pandoc` here. Rebuild the
requested output as a **new** document with docx-js when you can infer structure
from context; otherwise explain that in-place OOXML / tracked-changes editing
is not available in this sandbox.

## Minimal docx-js template (Harnex)

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
          text: "Title",
          heading: HeadingLevel.HEADING_1,
        }),
        new Paragraph({
          children: [new TextRun("Body text.")],
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

---

# DOCX creation, editing, and analysis

## Overview

A user may ask you to create, edit, or analyze the contents of a .docx file. A .docx file is essentially a ZIP archive containing XML files and other resources that you can read or edit. You have different tools and workflows available for different tasks.

## Workflow Decision Tree

### Reading/Analyzing Content
Use "Text extraction" or "Raw XML access" sections below

### Creating New Document
Use "Creating a new Word document" workflow

### Editing Existing Document
- **Your own document + simple changes**
  Use "Basic OOXML editing" workflow

- **Someone else's document**
  Use **"Redlining workflow"** (recommended default)

- **Legal, academic, business, or government docs**
  Use **"Redlining workflow"** (required)

## Reading and analyzing content

**Harnex:** `pandoc`, Python unpack scripts, and LibreOffice are **not** in the
sandbox. This section describes typical desktop workflows only.

### Text extraction
If you just need to read the text contents of a document, you should convert the document to markdown using pandoc. Pandoc provides excellent support for preserving document structure and can show tracked changes:

```bash
# Convert document to markdown with tracked changes
pandoc --track-changes=all path-to-file.docx -o output.md
# Options: --track-changes=accept/reject/all
```

### Raw XML access
You need raw XML access for: comments, complex formatting, document structure, embedded media, and metadata. For any of these features, you'll need to unpack a document and read its raw XML contents.

#### Unpacking a file
`python ooxml/scripts/unpack.py <office_file> <output_directory>`

#### Key file structures
* `word/document.xml` - Main document contents
* `word/comments.xml` - Comments referenced in document.xml
* `word/media/` - Embedded images and media files
* Tracked changes use `<w:ins>` (insertions) and `<w:del>` (deletions) tags

## Creating a new Word document

When creating a new Word document from scratch, use **docx-js**, which allows you to create Word documents using JavaScript/TypeScript.

### Workflow
1. Start from **Minimal docx-js template (Harnex)** above; extend it with
   `Paragraph`, `HeadingLevel`, `TextRun`, `Table`, `ImageRun`, and other
   `docx` exports as needed (the `docx` package is preinstalled).
2. Export with `Packer.toBuffer()` and write the buffer under
   `${HARNEX_OUTPUT_DIR}/<name>.docx`.

## Editing an existing Word document

**Harnex:** This skill runs **Node.js** only. The upstream **Document library**
(Python) workflow in this section **cannot be executed** in Harnex — do not
submit Python or shell commands to `execute`. Recreate content with docx-js or
set user expectations.

When editing outside Harnex, the upstream guide uses the **Document library**
(Python OOXML). That path is documented below for reference only.

### Workflow (upstream — not runnable in Harnex)
1. Read [`ooxml.md`](ooxml.md) for API patterns (file is **not** on the sandbox
   filesystem; embed guidance from your `search` instructions context only).
2. Unpack: `python ooxml/scripts/unpack.py <office_file> <output_directory>`
3. Python script using the Document library (see "Document Library" in ooxml.md)
4. Pack: `python ooxml/scripts/pack.py <input_directory> <office_file>`

## Redlining workflow for document review

**Harnex:** Requires `pandoc` and Python OOXML tools — **not available** here.
Use this section as background on tracked-change concepts only.

This workflow allows you to plan comprehensive tracked changes using markdown before implementing them in OOXML. **CRITICAL**: For complete tracked changes, you must implement ALL changes systematically.

**Batching Strategy**: Group related changes into batches of 3-10 changes. This makes debugging manageable while maintaining efficiency. Test each batch before moving to the next.

**Principle: Minimal, Precise Edits**
When implementing tracked changes, only mark text that actually changes. Repeating unchanged text makes edits harder to review and appears unprofessional. Break replacements into: [unchanged text] + [deletion] + [insertion] + [unchanged text]. Preserve the original run's RSID for unchanged text by extracting the `<w:r>` element from the original and reusing it.

Example - Changing "30 days" to "60 days" in a sentence:
```python
# BAD - Replaces entire sentence
'<w:del><w:r><w:delText>The term is 30 days.</w:delText></w:r></w:del><w:ins><w:r><w:t>The term is 60 days.</w:t></w:r></w:ins>'

# GOOD - Only marks what changed, preserves original <w:r> for unchanged text
'<w:r w:rsidR="00AB12CD"><w:t>The term is </w:t></w:r><w:del><w:r><w:delText>30</w:delText></w:r></w:del><w:ins><w:r><w:t>60</w:t></w:r></w:ins><w:r w:rsidR="00AB12CD"><w:t> days.</w:t></w:r>'
```

### Tracked changes workflow

1. **Get markdown representation**: Convert document to markdown with tracked changes preserved:
   ```bash
   pandoc --track-changes=all path-to-file.docx -o current.md
   ```

2. **Identify and group changes**: Review the document and identify ALL changes needed, organizing them into logical batches:

   **Location methods** (for finding changes in XML):
   - Section/heading numbers (e.g., "Section 3.2", "Article IV")
   - Paragraph identifiers if numbered
   - Grep patterns with unique surrounding text
   - Document structure (e.g., "first paragraph", "signature block")
   - **DO NOT use markdown line numbers** - they don't map to XML structure

   **Batch organization** (group 3-10 related changes per batch):
   - By section: "Batch 1: Section 2 amendments", "Batch 2: Section 5 updates"
   - By type: "Batch 1: Date corrections", "Batch 2: Party name changes"
   - By complexity: Start with simple text replacements, then tackle complex structural changes
   - Sequential: "Batch 1: Pages 1-3", "Batch 2: Pages 4-6"

3. **Read documentation and unpack**:
   - Review OOXML / Document library patterns from your context (no on-disk `ooxml.md` in Harnex).
   - **Unpack the document**: `python ooxml/scripts/unpack.py <file.docx> <dir>`
   - **Note the suggested RSID**: The unpack script will suggest an RSID to use for your tracked changes. Copy this RSID for use in step 4b.

4. **Implement changes in batches**: Group changes logically (by section, by type, or by proximity) and implement them together in a single script. This approach:
   - Makes debugging easier (smaller batch = easier to isolate errors)
   - Allows incremental progress
   - Maintains efficiency (batch size of 3-10 changes works well)

   **Suggested batch groupings:**
   - By document section (e.g., "Section 3 changes", "Definitions", "Termination clause")
   - By change type (e.g., "Date changes", "Party name updates", "Legal term replacements")
   - By proximity (e.g., "Changes on pages 1-3", "Changes in first half of document")

   For each batch of related changes:

   **a. Map text to XML**: Grep for text in `word/document.xml` to verify how text is split across `<w:r>` elements.

   **b. Create and run script**: Use `get_node` to find nodes, implement changes, then `doc.save()`. See **"Document Library"** section in ooxml.md for patterns.

   **Note**: Always grep `word/document.xml` immediately before writing a script to get current line numbers and verify text content. Line numbers change after each script run.

5. **Pack the document**: After all batches are complete, convert the unpacked directory back to .docx:
   ```bash
   python ooxml/scripts/pack.py unpacked reviewed-document.docx
   ```

6. **Final verification**: Do a comprehensive check of the complete document:
   - Convert final document to markdown:
     ```bash
     pandoc --track-changes=all reviewed-document.docx -o verification.md
     ```
   - Verify ALL changes were applied correctly:
     ```bash
     grep "original phrase" verification.md  # Should NOT find it
     grep "replacement phrase" verification.md  # Should find it
     ```
   - Check that no unintended changes were introduced


## Converting Documents to Images

**Harnex:** `soffice` and `pdftoppm` are **not** in the sandbox — reference only.

To visually analyze Word documents, convert them to images using a two-step process:

1. **Convert DOCX to PDF**:
   ```bash
   soffice --headless --convert-to pdf document.docx
   ```

2. **Convert PDF pages to JPEG images**:
   ```bash
   pdftoppm -jpeg -r 150 document.pdf page
   ```
   This creates files like `page-1.jpg`, `page-2.jpg`, etc.

Options:
- `-r 150`: Sets resolution to 150 DPI (adjust for quality/size balance)
- `-jpeg`: Output JPEG format (use `-png` for PNG if preferred)
- `-f N`: First page to convert (e.g., `-f 2` starts from page 2)
- `-l N`: Last page to convert (e.g., `-l 5` stops at page 5)
- `page`: Prefix for output files

Example for specific range:
```bash
pdftoppm -jpeg -r 150 -f 2 -l 5 document.pdf page  # Converts only pages 2-5
```

## Code Style Guidelines
**IMPORTANT**: When generating code for DOCX operations:
- Write concise code
- Avoid verbose variable names and redundant operations
- Avoid unnecessary print statements

## Dependencies

**Harnex (docx built-in):** only `docx` (npm) is guaranteed on the execute path.

Upstream / local workstation dependencies (not provisioned in Harnex):

Required dependencies (install if not available):

- **pandoc**: `sudo apt-get install pandoc` (for text extraction)
- **docx**: `npm install -g docx` (for creating new documents)
- **LibreOffice**: `sudo apt-get install libreoffice` (for PDF conversion)
- **Poppler**: `sudo apt-get install poppler-utils` (for pdftoppm to convert PDF to images)
- **defusedxml**: `pip install defusedxml` (for secure XML parsing)
