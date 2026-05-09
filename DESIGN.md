# DESIGN.md — Harnex Console

Design system for the Harnex admin console (`web/`). All UI decisions calibrate against this document.

---

## Design Tokens

### Color System

CSS variables defined in `web/src/styles/globals.css`. Light and dark themes via `[data-theme="dark"]`.

#### Surface Colors

| Variable | Light | Dark | Purpose |
|----------|-------|------|---------|
| `--bg` | `#F5F5F0` | `#0E0E10` | Page background |
| `--bg-alt` | `#FAFAF7` | `#141418` | Alternate background (row hover, subtle sections) |
| `--surface` | `#FFFFFF` | `#18181C` | Card/container background |
| `--surface-2` | `#FBFAF6` | `#1C1C21` | Secondary surface (sidebar, table headers) |

#### Text Colors

| Variable | Light | Dark | Purpose |
|----------|-------|------|---------|
| `--ink` | `#0A0A0A` | `#F4F3EE` | Primary text |
| `--ink-2` | `#1F1F22` | `#E4E3DD` | Secondary text |
| `--slate` | `#3F3F46` | `#B8B6AE` | Tertiary text / labels |
| `--muted` | `#71717A` | `#82817A` | Muted / hint text |
| `--muted-2` | `#A1A1AA` | `#5C5B55` | Very muted / disabled |

#### Border Colors

| Variable | Light | Dark | Purpose |
|----------|-------|------|---------|
| `--border` | `#E7E5E0` | `#2A2A2F` | Default border |
| `--border-strong` | `#D4D2CC` | `#3A3A40` | Stronger border (hover, focus) |
| `--border-soft` | `#EFEDE7` | `#222227` | Soft border (table rows) |

#### Accent (Orange)

| Variable | Light | Dark | Purpose |
|----------|-------|------|---------|
| `--accent` | `#F97316` | `#FB923C` | Primary accent |
| `--accent-hover` | `#EA580C` | `#F97316` | Accent hover state |
| `--accent-soft` | `#FFF1E6` | `rgba(251,146,60,0.12)` | Accent background (badges) |
| `--accent-border` | `#FED7AA` | `rgba(251,146,60,0.30)` | Accent border |
| `--accent-ink` | `#9A3412` | `#FFD4B0` | Text on accent background |

#### Semantic Colors

| Purpose | Variable | Light | Dark |
|---------|----------|-------|------|
| Success | `--green` | `#16A34A` | `#4ADE80` |
| Success bg | `--green-soft` | `#DCFCE7` | `rgba(74,222,128,0.12)` |
| Success border | `--green-border` | `#BBF7D0` | `rgba(74,222,128,0.30)` |
| Success text | `--green-ink` | `#14532D` | `#BBF7D0` |
| Warning | `--amber` | `#D97706` | `#FBBF24` |
| Warning bg | `--amber-soft` | `#FEF3C7` | `rgba(251,191,36,0.12)` |
| Warning border | `--amber-border` | `#FDE68A` | `rgba(251,191,36,0.30)` |
| Warning text | `--amber-ink` | `#78350F` | `#FDE68A` |
| Error | `--red` | `#DC2626` | `#F87171` |
| Error bg | `--red-soft` | `#FEE2E2` | `rgba(248,113,113,0.12)` |
| Error border | `--red-border` | `#FECACA` | `rgba(248,113,113,0.30)` |
| Error text | `--red-ink` | `#7F1D1D` | `#FECACA` |

### Typography

| Token | Stack | Usage |
|-------|-------|-------|
| `--font-sans` | Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif | Body, UI, labels |
| `--font-serif` | Newsreader, Tiempos, Georgia, serif | Decorative italic ("serif-i") |
| `--font-mono` | JetBrains Mono, SF Mono, Menlo, Consolas, monospace | Code, tokens, keys, prefixes |

**Utility classes:** `.mono` (monospace), `.serif-i` (serif italic), `.kicker` (uppercase section label, 11.5px, muted)

### Spacing / Radius

| Token | Value | Usage |
|-------|-------|-------|
| `--r-sm` | 4px | Badges, small elements |
| `--r-md` | 6px | Buttons, inputs, selects |
| `--r-lg` | 8px | Cards |
| `--r-xl` | 12px | Large containers |

### Shadows

| Token | Light | Dark |
|-------|-------|------|
| `--shadow-sm` | `0 1px 2px rgba(20,16,8,0.04)` | `0 1px 2px rgba(0,0,0,0.4)` |
| `--shadow-md` | `0 1px 3px rgba(20,16,8,0.06), 0 1px 2px rgba(20,16,8,0.04)` | `0 1px 3px rgba(0,0,0,0.5), 0 1px 2px rgba(0,0,0,0.4)` |
| `--shadow-lg` | `0 4px 12px rgba(20,16,8,0.06), 0 2px 4px rgba(20,16,8,0.04)` | `0 8px 24px rgba(0,0,0,0.55), 0 2px 6px rgba(0,0,0,0.4)` |

---

## Component Rules

### Cards

- **Rule:** Cards earn their existence. Only use `.card` when the card IS the interaction (connection summary, key detail). Forms are NOT cards — use section layout with headers.
- **Class:** `.card` — applies surface background, border, and `--r-lg` radius. No padding by default.

### Buttons

- **Base:** `.btn` (32px height, 13px text, `--r-md` radius) + variant class
- **Variants:** `.btn-primary` (filled ink), `.btn-accent` (filled orange), `.btn-ghost` (transparent + border), `.btn-secondary` (surface bg), `.btn-danger` (red text/soft bg)
- **Sizes:** `.btn-sm` (26px), `.btn-lg` (40px)

### Inputs

- **Use:** `<Input>` component from `web/src/components/ui/Input.tsx` — never raw `<input className="input">` in new code.
- **Select:** `<Select>` component from `web/src/components/ui/Select.tsx`.

### Form Fields

- **Use:** `<Field>` component from `web/src/components/ui/Field.tsx` — single shared implementation. Props: `label`, `htmlFor`, `hint?`, `error?`.
- **Do NOT** define inline Field/FormField components in page files.

### Badges

- **Classes:** `.badge` + color variant (`.badge-green`, `.badge-amber`, `.badge-red`, `.badge-slate`, `.badge-accent`)
- **With dot:** Include `<span className="badge-dot" />` inside badge for status dots.
- **Mono:** Add `.badge-mono` for monospace badges (prefixes, IDs).

### Alerts

- **Classes:** `.alert` + color variant (`.alert-red`, `.alert-amber`, `.alert-info`, `.alert-accent`)
- **Structure:** Flex row with icon + content.

### Tables

- **Class:** `.tbl` — full-width, collapsed borders, `--surface-2` header, `--border-soft` row dividers.
- **Row hover:** Add `.row-hover` to `<tr>` for hover highlight.

---

## Layout Patterns

### App Shell

- **Sidebar:** 220px fixed, collapsible at 1024px breakpoint. Dark surface-2 bg, border-right.
- **Topbar:** 44px height, border-bottom, page title + actions.
- **Content:** Flex column, overflow auto, 20px padding.

### Connection Wizard

- **Stepper:** 3 steps with numbered circles (filled when active/complete, outlined otherwise).
- **Step 1 (Choose):** 2-column grid of connector tiles (icon, name, description, check on selected).
- **Step 2 (Configure):** Connector-specific form — section headers, NOT card wrappers.
- **Step 3 (Review):** Real form state summary, NOT hardcoded strings.

### Forms

- **Layout:** Flex column, 12-14px gap between fields.
- **Labels:** 12.5px, 500 weight, `--slate` color.
- **Hints:** 11.5px, `--muted` color, below input.
- **Errors:** 11.5px, `--red` color, below input (replaces hint).

---

## Design Principles

1. **App UI, not marketing.** Calm surface hierarchy, strong typography, few colors. Dense but readable.
2. **Cards earn existence.** No decorative card grids. Only card-wrap when the card IS the interaction.
3. **Subtraction default.** If a UI element doesn't earn its pixels, cut it.
4. **Every state is designed.** Loading, empty, error, success, partial — all specified before implementation.
5. **Accessibility is not optional.** 44px touch targets, keyboard nav, aria-live for dynamic content, 4.5:1 minimum contrast.
6. **One Field component.** Never define inline Field/FormField components in page files.
7. **Tokens over raw values.** Use CSS variables, never hardcoded hex colors in components.
