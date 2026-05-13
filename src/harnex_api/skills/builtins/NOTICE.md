# Vendored skill content

The SKILL.md authoring guides and helper scripts under `pdf/`, `docx/`,
`xlsx/`, and `pptx/` (excluding the Harnex sandbox-contract preamble at the
top of each `SKILL.md`, and our `skill.yaml` manifests) are vendored from
Composio's open-source [`awesome-claude-skills`][upstream] repository under
its MIT License. Per-skill `LICENSE.txt` files are kept alongside the
content.

When upstream content changes meaningfully (new sections, library shifts,
breaking script changes), refresh by replacing the contents of each
`<skill>/` directory while preserving:

- `skill.yaml` (Harnex manifest)
- the `# Harnex sandbox contract — READ THIS FIRST` preamble at the top of
  each `SKILL.md`

The `ooxml/schemas/` subdirectory (~1 MB of OOXML XSDs) is intentionally
**excluded** from the vendored copy. The Blaxel sandbox does not have
filesystem access to skill assets at runtime, so the schemas are not useful
in our flow.

[upstream]: https://github.com/composiohq/awesome-claude-skills
