import { Link, createFileRoute } from "@tanstack/react-router";
import type { CSSProperties, ReactNode } from "react";
import {
  ArrowRight,
  BookOpen,
  Check,
  Copy,
  Download,
  Lock,
  Moon,
  RefreshCw,
  Search,
  Sun,
  Trash2,
} from "lucide-react";

import { HarnexLogo } from "@/components/HarnexLogo";
import { useAuth } from "@/lib/auth";
import { useTheme } from "@/lib/theme";

export const Route = createFileRoute("/skills")({
  component: SkillsMarketingPage,
});

// ── Data ──────────────────────────────────────────────────────────────────────

type SkillTone = { bg: string; border: string; ink: string };

type Skill = {
  id: "pdf" | "docx" | "xlsx" | "pptx";
  ext: string;
  name: string;
  full: string;
  tone: SkillTone;
  desc: string;
  bullets: string[];
  sampleName: string;
  size: string;
};

const SKILL_PDF: Skill = {
  id: "pdf",
  ext: "pdf",
  name: "PDF",
  full: "Portable Document Format",
  tone: { bg: "var(--red-soft)", border: "var(--red-border)", ink: "var(--red-ink)" },
  desc:
    "Reports, invoices, statements, contracts — anything destined for print or signature.",
  bullets: [
    "Markdown body with page-level CSS",
    "Headers, footers, page numbers",
    "Embedded images and signed links",
  ],
  sampleName: "q1-revenue-summary.pdf",
  size: "1.2 MB",
};

const SKILL_DOCX: Skill = {
  id: "docx",
  ext: "docx",
  name: "Word",
  full: "Microsoft Word document",
  tone: { bg: "#EFF6FF", border: "#BFDBFE", ink: "#1E3A8A" },
  desc: "Native .docx the recipient can open in Word, Pages, or Google Docs and keep editing.",
  bullets: [
    "Styles, headings, lists, tables",
    "Comments and tracked changes",
    "Sections, columns, footnotes",
  ],
  sampleName: "acme-msa-draft.docx",
  size: "84 KB",
};

const SKILL_XLSX: Skill = {
  id: "xlsx",
  ext: "xlsx",
  name: "Excel",
  full: "Microsoft Excel workbook",
  tone: { bg: "var(--green-soft)", border: "var(--green-border)", ink: "var(--green-ink)" },
  desc:
    "Multi-sheet workbooks with real formulas — not flat CSVs in a different file extension.",
  bullets: [
    "Formulas, named ranges, validation",
    "Conditional formatting, freeze panes",
    "Charts and pivot tables",
  ],
  sampleName: "weekly-pipeline.xlsx",
  size: "210 KB",
};

const SKILL_PPTX: Skill = {
  id: "pptx",
  ext: "pptx",
  name: "PowerPoint",
  full: "Microsoft PowerPoint deck",
  tone: { bg: "var(--accent-soft)", border: "var(--accent-border)", ink: "var(--accent-ink)" },
  desc:
    "Slide decks with native text boxes, shapes, and speaker notes — editable in PowerPoint or Keynote.",
  bullets: [
    "Native shapes and text frames",
    "Master slides and layouts",
    "Speaker notes per slide",
  ],
  sampleName: "board-update-may.pptx",
  size: "1.8 MB",
};

const SKILLS: readonly Skill[] = [SKILL_PDF, SKILL_DOCX, SKILL_XLSX, SKILL_PPTX];

/** Public repo docs — README (stack, MCP smoke, local dev). */
const HARNEX_REPO_README =
  "https://github.com/pranavvp16/harnex/blob/main/README.md";
/** Developer / MCP surface spec shipped in-repo. */
const HARNEX_DEV_SPEC = "https://github.com/pranavvp16/harnex/blob/main/CLAUDE.md";

const FLOW_STEPS = [
  {
    n: "01",
    kicker: "Search",
    title: "Find the skill",
    body:
      "The agent calls search with skills:true. Harnex returns the matching skill — its slug, its authoring guide, and the shape of its inputs.",
    io: { call: "search({ q, skills: true })", out: "skills/pdf  +  guide" },
  },
  {
    n: "02",
    kicker: "Write code",
    title: "Author the document",
    body:
      "Following the skill's guide, the agent writes the body as code: markdown, table data, slide layouts. Inputs are typed; no spec-guessing.",
    io: { call: "compose(body, styles, meta)", out: "validated payload" },
  },
  {
    n: "03",
    kicker: "Execute",
    title: "Run in an isolated sandbox",
    body:
      "Harnex executes the code in a per-tenant sandbox: ephemeral filesystem, no network, one process. Errors return as data, never as silent failures.",
    io: { call: 'execute("skills/pdf", payload)', out: "200 OK · 1.1 s" },
  },
  {
    n: "04",
    kicker: "Download",
    title: "Hand the file to the user",
    body:
      "The response carries a short-lived signed URL the agent can paste straight into chat. The same file lands on the Files dashboard for retention and audit.",
    io: { call: "→ download_url, expires_at", out: "Files dashboard" },
  },
] as const;

const FILES_PREVIEW: { name: string; skill: Skill; size: string; when: string; by: string }[] = [
  { name: "q1-revenue-summary.pdf", skill: SKILL_PDF, size: "1.2 MB", when: "12 min ago", by: "agent · ops-bot" },
  { name: "board-update-may.pptx", skill: SKILL_PPTX, size: "1.8 MB", when: "1 h ago", by: "agent · briefing" },
  { name: "weekly-pipeline.xlsx", skill: SKILL_XLSX, size: "210 KB", when: "3 h ago", by: "scheduled · friday" },
  { name: "acme-msa-draft.docx", skill: SKILL_DOCX, size: "84 KB", when: "yesterday", by: "agent · legal-bot" },
  { name: "oct-invoices.pdf", skill: SKILL_PDF, size: "640 KB", when: "2 days ago", by: "agent · billing" },
  { name: "onboarding-checklist.docx", skill: SKILL_DOCX, size: "32 KB", when: "4 days ago", by: "agent · hr-bot" },
];

// ── Atoms ─────────────────────────────────────────────────────────────────────

function SkillGlyph({ skill, size = 56 }: { skill: Skill; size?: number }) {
  return (
    <div
      style={{
        width: size,
        height: size,
        flexShrink: 0,
        background: skill.tone.bg,
        border: `1px solid ${skill.tone.border}`,
        borderRadius: 6,
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        fontFamily: "var(--font-mono)",
        fontSize: Math.round(size * 0.27),
        fontWeight: 600,
        color: skill.tone.ink,
        letterSpacing: "0.04em",
      }}
    >
      {skill.ext}
    </div>
  );
}

function InlineMono({ children, size = 13 }: { children: ReactNode; size?: number }) {
  return (
    <span
      className="mono"
      style={{
        background: "var(--surface)",
        border: "1px solid var(--border)",
        padding: "2px 6px",
        borderRadius: 4,
        fontSize: size,
      }}
    >
      {children}
    </span>
  );
}

const SECTION_MAX = 1120;
const SECTION_PAD: CSSProperties = { maxWidth: SECTION_MAX, margin: "0 auto", padding: "80px 32px" };

// ── Page ──────────────────────────────────────────────────────────────────────

function SkillsMarketingPage() {
  const auth = useAuth();
  const isAuthed = auth.status === "authenticated";
  const { theme, toggle: toggleTheme } = useTheme();

  return (
    <>
      <div className="bg-atmosphere" aria-hidden="true" />
      <div className="bg-grid" aria-hidden="true" />
      <div
        style={{
          minHeight: "100vh",
          display: "flex",
          flexDirection: "column",
          position: "relative",
          zIndex: 1,
          overflowX: "hidden",
        }}
      >
        <SkillsHeader theme={theme} toggleTheme={toggleTheme} isAuthed={isAuthed} />

        <SkillsHero isAuthed={isAuthed} />
        <SkillsFlow />
        <SkillsCatalog isAuthed={isAuthed} />
        <SkillsFiles />
        <SkillsCallout isAuthed={isAuthed} />

        <footer style={{ borderTop: "1px solid var(--border)", marginTop: "auto" }}>
          <div
            style={{
              maxWidth: SECTION_MAX,
              margin: "0 auto",
              padding: "24px 32px",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <HarnexLogo size={20} />
              <span style={{ fontSize: 12, color: "var(--muted)" }}>© {new Date().getFullYear()}</span>
            </div>
            <nav style={{ display: "flex", gap: 16 }}>
              {(
                [
                  ["Docs", HARNEX_REPO_README],
                  ["Changelog", "https://github.com/pranavvp16/harnex/releases"],
                  ["Status", HARNEX_REPO_README],
                  ["Privacy", "#"],
                  ["Terms", "#"],
                ] as const
              ).map(([label, href]) => (
                <a
                  key={label}
                  href={href}
                  {...(href.startsWith("http")
                    ? { target: "_blank", rel: "noopener noreferrer" }
                    : {})}
                  style={{ fontSize: 13, color: "var(--muted)", fontWeight: 500, textDecoration: "none" }}
                >
                  {label}
                </a>
              ))}
            </nav>
          </div>
        </footer>
      </div>
    </>
  );
}

// ── Header ────────────────────────────────────────────────────────────────────

function SkillsHeader({
  theme,
  toggleTheme,
  isAuthed,
}: {
  theme: string;
  toggleTheme: () => void;
  isAuthed: boolean;
}) {
  return (
    <header
      style={{
        position: "sticky",
        top: 0,
        zIndex: 20,
        borderBottom: "1px solid var(--border)",
        background: theme === "dark" ? "rgba(14,14,16,0.88)" : "rgba(245,245,240,0.85)",
        backdropFilter: "blur(12px)",
        WebkitBackdropFilter: "blur(12px)",
      }}
    >
      <div
        className="marketing-header-inner"
        style={{
          maxWidth: SECTION_MAX,
          margin: "0 auto",
          padding: "0 32px",
          height: 52,
          display: "flex",
          alignItems: "center",
          gap: 24,
        }}
      >
        <Link to="/home" style={{ display: "inline-flex" }}>
          <HarnexLogo size={22} />
        </Link>
        <nav className="marketing-nav">
          <Link
            to="/home"
            style={{
              fontSize: 13.5,
              fontWeight: 500,
              color: "var(--slate)",
              padding: "5px 10px",
              borderRadius: "var(--r-sm)",
              textDecoration: "none",
            }}
          >
            Home
          </Link>
          <span
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 6,
              fontSize: 13.5,
              fontWeight: 500,
              color: "var(--ink)",
              padding: "5px 10px",
              borderRadius: "var(--r-sm)",
            }}
          >
            Skills
            <span
              style={{
                fontSize: 9.5,
                padding: "1px 5px",
                borderRadius: 3,
                background: "var(--accent-soft)",
                color: "var(--accent-ink)",
                border: "1px solid var(--accent-border)",
                textTransform: "uppercase",
                letterSpacing: "0.06em",
                fontWeight: 600,
              }}
            >
              New
            </span>
          </span>
          {["How it works", "Security", "Pricing"].map((l) => (
            <Link
              key={l}
              to="/home"
              hash={l.toLowerCase().replace(/ /g, "-")}
              style={{
                fontSize: 13.5,
                fontWeight: 500,
                color: "var(--slate)",
                padding: "5px 10px",
                borderRadius: "var(--r-sm)",
                textDecoration: "none",
              }}
            >
              {l}
            </Link>
          ))}
          <a
            href={HARNEX_REPO_README}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              fontSize: 13.5,
              fontWeight: 500,
              color: "var(--slate)",
              padding: "5px 10px",
              borderRadius: "var(--r-sm)",
              textDecoration: "none",
            }}
          >
            Docs
          </a>
        </nav>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <button
            className="btn btn-ghost btn-sm"
            style={{ width: 30, padding: 0 }}
            onClick={toggleTheme}
            title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
          >
            {theme === "dark" ? <Sun size={13} /> : <Moon size={13} />}
          </button>
          {isAuthed ? (
            <Link to="/dashboard" className="btn btn-ghost btn-sm">
              Console →
            </Link>
          ) : (
            <Link to="/onboarding" className="btn btn-accent btn-sm">
              Get started →
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}

// ── Hero ──────────────────────────────────────────────────────────────────────

function SkillsHero({ isAuthed }: { isAuthed: boolean }) {
  const cta = isAuthed ? (
    <Link to="/dashboard" className="btn btn-primary btn-lg">
      Try it in the console <ArrowRight size={14} />
    </Link>
  ) : (
    <Link to="/onboarding" className="btn btn-primary btn-lg">
      Try it in the console <ArrowRight size={14} />
    </Link>
  );

  return (
    <section style={{ maxWidth: SECTION_MAX, margin: "0 auto", padding: "72px 32px 56px" }}>
      <div
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: 6,
          padding: "5px 10px",
          border: "1px solid var(--border)",
          borderRadius: 999,
          background: "var(--surface)",
          fontSize: 12,
          color: "var(--slate)",
          marginBottom: 28,
        }}
      >
        <span style={{ width: 6, height: 6, borderRadius: 999, background: "var(--accent)" }} />
        <span>Document Skills</span>
        <span style={{ color: "var(--muted)" }}>·</span>
        <span style={{ color: "var(--muted)" }} className="mono">v0.4</span>
      </div>

      <h1
        style={{
          fontSize: "clamp(44px, 7vw, 72px)",
          fontWeight: 500,
          letterSpacing: "-0.03em",
          lineHeight: 1.05,
          margin: "0 0 22px",
          maxWidth: 1000,
          color: "var(--ink)",
        }}
      >
        Documents — through the<br />
        <span className="serif-i">same</span> two tools.
      </h1>

      <p
        style={{
          fontSize: 18,
          color: "var(--slate)",
          maxWidth: 660,
          margin: "0 0 32px",
          lineHeight: 1.5,
        }}
      >
        Skills extend Harnex MCP with first-class authoring for PDFs, Word docs, Excel sheets, and
        PowerPoint decks. Agents call <InlineMono size={14}>search</InlineMono> to find the right
        skill, then <InlineMono size={14}>execute</InlineMono> to generate the file. Same auth,
        same tenant isolation, same MCP surface.
      </p>

      <div style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: 56, flexWrap: "wrap" }}>
        {cta}
        <a
          className="btn btn-ghost btn-lg"
          href={HARNEX_DEV_SPEC}
          target="_blank"
          rel="noopener noreferrer"
        >
          <BookOpen size={14} /> Read the spec
        </a>
        <span style={{ fontSize: 13, color: "var(--muted)" }}>
          <InlineMono size={11.5}>npm i @harnex/mcp@0.4</InlineMono>
        </span>
      </div>

      <SkillsHeroPanel />
    </section>
  );
}

function SkillsHeroPanel() {
  return (
    <div
      style={{
        border: "1px solid var(--border)",
        borderRadius: 12,
        background: "var(--surface)",
        boxShadow: "var(--shadow-lg)",
        overflow: "hidden",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          padding: "10px 14px",
          borderBottom: "1px solid var(--border)",
          background: "var(--surface-2)",
        }}
      >
        <div style={{ display: "flex", gap: 6 }}>
          {[0, 1, 2].map((i) => (
            <span
              key={i}
              style={{
                width: 11,
                height: 11,
                borderRadius: 999,
                background: "#E5E5E0",
                border: "1px solid var(--border)",
              }}
            />
          ))}
        </div>
        <div
          className="mono"
          style={{ flex: 1, textAlign: "center", fontSize: 12, color: "var(--muted)" }}
        >
          mcp · agent transcript
        </div>
        <span className="mono" style={{ fontSize: 11, color: "var(--muted)" }}>1.4s · 2 tools</span>
      </div>

      <div className="skills-hero-grid">
        <div
          style={{
            padding: 22,
            fontFamily: "var(--font-mono)",
            fontSize: 12,
            lineHeight: 1.65,
            color: "var(--slate)",
            display: "flex",
            flexDirection: "column",
            gap: 14,
          }}
        >
          <div>
            <div style={{ color: "var(--muted)" }}>{">"} agent</div>
            <div style={{ color: "var(--ink)" }}>search({"{"}</div>
            <div style={{ paddingLeft: 14 }}>
              q: <span style={{ color: "var(--accent-ink)" }}>"summary report as pdf"</span>,
            </div>
            <div style={{ paddingLeft: 14 }}>
              skills: <span style={{ color: "var(--accent-ink)" }}>true</span>
            </div>
            <div style={{ color: "var(--ink)" }}>{"}"})</div>
          </div>
          <div>
            <div style={{ color: "var(--muted)" }}>← harnex · 312 ms</div>
            <div>{"{"}</div>
            <div style={{ paddingLeft: 14 }}>
              skill: <span style={{ color: "var(--accent-ink)" }}>"skills/pdf"</span>,
            </div>
            <div style={{ paddingLeft: 14 }}>
              guide: <span style={{ color: "var(--muted)" }}>"&lt;authoring prompt …&gt;"</span>,
            </div>
            <div style={{ paddingLeft: 14 }}>
              inputs: [<span style={{ color: "var(--ink)" }}>"body"</span>,{" "}
              <span style={{ color: "var(--ink)" }}>"styles"</span>,{" "}
              <span style={{ color: "var(--ink)" }}>"meta"</span>]
            </div>
            <div>{"}"}</div>
          </div>
          <div>
            <div style={{ color: "var(--muted)" }}>{">"} agent</div>
            <div style={{ color: "var(--ink)" }}>
              execute(<span style={{ color: "var(--accent-ink)" }}>"skills/pdf"</span>, {"{"}
            </div>
            <div style={{ paddingLeft: 14 }}>
              body: <span style={{ color: "var(--muted)" }}>"# Q1 Revenue …"</span>,
            </div>
            <div style={{ paddingLeft: 14 }}>styles: {'{ pageSize: "A4" }'}</div>
            <div style={{ color: "var(--ink)" }}>{"}"})</div>
          </div>
        </div>

        <div
          style={{
            padding: 22,
            display: "flex",
            flexDirection: "column",
            gap: 14,
            background: "var(--bg-alt)",
          }}
        >
          <div className="kicker">Response</div>
          <div
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: 12,
              lineHeight: 1.65,
              color: "var(--slate)",
            }}
          >
            <div style={{ color: "var(--muted)" }}>← harnex · execute · 1.1 s</div>
            <div style={{ color: "var(--ink)" }}>{"{"}</div>
            <div style={{ paddingLeft: 14 }}>
              file_id: <span style={{ color: "var(--accent-ink)" }}>"fl_2K9p4mZ"</span>,
            </div>
            <div style={{ paddingLeft: 14 }}>
              skill: <span style={{ color: "var(--accent-ink)" }}>"skills/pdf"</span>,
            </div>
            <div style={{ paddingLeft: 14 }}>
              bytes: <span style={{ color: "var(--ink)" }}>1_247_104</span>,
            </div>
            <div style={{ paddingLeft: 14 }}>
              download_url: <span style={{ color: "var(--accent-ink)" }}>"https://…"</span>,
            </div>
            <div style={{ paddingLeft: 14 }}>
              expires_at: <span style={{ color: "var(--ink)" }}>"2026-05-13T18:42Z"</span>
            </div>
            <div style={{ color: "var(--ink)" }}>{"}"}</div>
          </div>

          <div
            style={{
              border: "1px solid var(--border)",
              borderRadius: 8,
              padding: "12px 14px",
              background: "var(--surface)",
              display: "flex",
              alignItems: "center",
              gap: 12,
            }}
          >
            <SkillGlyph skill={SKILL_PDF} size={40} />
            <div style={{ flex: 1, minWidth: 0 }}>
              <div
                className="mono"
                style={{
                  fontSize: 12.5,
                  color: "var(--ink)",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap",
                }}
              >
                q1-revenue-summary.pdf
              </div>
              <div style={{ fontSize: 11, color: "var(--muted)" }}>1.2 MB · expires in 15 min</div>
            </div>
            <button className="btn btn-secondary btn-sm">
              <Download size={12} /> Download
            </button>
          </div>

          <div
            style={{
              fontSize: 11.5,
              color: "var(--muted)",
              display: "flex",
              alignItems: "center",
              gap: 6,
            }}
          >
            <span style={{ color: "var(--accent)", display: "inline-flex" }}>
              <Lock size={12} />
            </span>
            Signed URL · single-tenant sandbox · no key material in the response
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Flow ──────────────────────────────────────────────────────────────────────

function SkillsFlow() {
  return (
    <section style={{ borderTop: "1px solid var(--border)", background: "var(--bg-alt)" }}>
      <div style={SECTION_PAD}>
        <div style={{ marginBottom: 48 }}>
          <span className="kicker">How it works</span>
          <h2
            style={{
              fontSize: 44,
              fontWeight: 500,
              letterSpacing: "-0.03em",
              lineHeight: 1.05,
              margin: "12px 0 0",
              maxWidth: 760,
              color: "var(--ink)",
            }}
          >
            Four steps. <span className="serif-i">Two tools.</span> One signed URL.
          </h2>
        </div>
        <div
          className="skills-flow-grid"
          style={{
            border: "1px solid var(--border)",
            borderRadius: 12,
            background: "var(--surface)",
            overflow: "hidden",
          }}
        >
          {FLOW_STEPS.map((s, i) => (
            <div
              key={s.n}
              className="skills-flow-cell"
              style={{
                padding: 24,
                borderRight: i < FLOW_STEPS.length - 1 ? "1px solid var(--border)" : "none",
                display: "flex",
                flexDirection: "column",
                gap: 12,
              }}
            >
              <div style={{ display: "flex", alignItems: "baseline", gap: 8 }}>
                <span
                  className="mono"
                  style={{ fontSize: 11, color: "var(--accent)", fontWeight: 600 }}
                >
                  {s.n}
                </span>
                <span className="kicker">{s.kicker}</span>
                <span
                  style={{ flex: 1, height: 1, background: "var(--border)", marginLeft: 4 }}
                />
              </div>
              <h3
                style={{
                  fontSize: 20,
                  fontWeight: 500,
                  letterSpacing: "-0.01em",
                  margin: 0,
                  color: "var(--ink)",
                }}
              >
                {s.title}
              </h3>
              <p
                style={{
                  fontSize: 13.5,
                  color: "var(--slate)",
                  margin: "0 0 4px",
                  lineHeight: 1.55,
                }}
              >
                {s.body}
              </p>
              <div
                style={{
                  marginTop: "auto",
                  borderTop: "1px solid var(--border-soft)",
                  paddingTop: 12,
                  display: "flex",
                  flexDirection: "column",
                  gap: 6,
                  fontSize: 11.5,
                  fontFamily: "var(--font-mono)",
                }}
              >
                <div style={{ color: "var(--muted)" }}>
                  {">"} <span style={{ color: "var(--ink)" }}>{s.io.call}</span>
                </div>
                <div style={{ color: "var(--muted)" }}>
                  ← <span style={{ color: "var(--slate)" }}>{s.io.out}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ── Catalog ───────────────────────────────────────────────────────────────────

function SkillsCatalog({ isAuthed }: { isAuthed: boolean }) {
  const tryTo = isAuthed ? "/dashboard" : "/onboarding";
  return (
    <section style={SECTION_PAD}>
      <div
        style={{
          marginBottom: 48,
          display: "flex",
          alignItems: "flex-end",
          justifyContent: "space-between",
          gap: 24,
          flexWrap: "wrap",
        }}
      >
        <div>
          <span className="kicker">Built-in skills</span>
          <h2
            style={{
              fontSize: 44,
              fontWeight: 500,
              letterSpacing: "-0.03em",
              lineHeight: 1.05,
              margin: "12px 0 0",
              maxWidth: 720,
              color: "var(--ink)",
            }}
          >
            Four formats, <span className="serif-i">shipped</span>.
          </h2>
          <p
            style={{
              fontSize: 15,
              color: "var(--slate)",
              margin: "14px 0 0",
              maxWidth: 580,
              lineHeight: 1.55,
            }}
          >
            Every connection gets these four out of the box. Custom skills land later this quarter.
          </p>
        </div>
        <span
          className="mono"
          style={{ display: "inline-flex", alignItems: "center", gap: 6, fontSize: 12.5, color: "var(--muted)" }}
        >
          4 / 4 ready · custom skills · soon
        </span>
      </div>

      <div className="responsive-grid-2" style={{ gap: 16 }}>
        {SKILLS.map((s) => (
          <article key={s.id} className="card" style={{ padding: 26, display: "flex", flexDirection: "column", gap: 16 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
              <SkillGlyph skill={s} size={52} />
              <div style={{ flex: 1, minWidth: 0 }}>
                <h3
                  style={{
                    fontSize: 22,
                    fontWeight: 500,
                    letterSpacing: "-0.01em",
                    margin: 0,
                    color: "var(--ink)",
                  }}
                >
                  {s.name}
                </h3>
                <div className="mono" style={{ fontSize: 12, color: "var(--muted)", marginTop: 2 }}>
                  skills/{s.id} <span style={{ color: "var(--muted-2)" }}>·</span> {s.full}
                </div>
              </div>
              <span className="badge badge-green"><span className="badge-dot" />Ready</span>
            </div>

            <p style={{ fontSize: 13.5, color: "var(--slate)", margin: 0, lineHeight: 1.55 }}>{s.desc}</p>

            <div
              style={{
                display: "flex",
                flexDirection: "column",
                gap: 6,
                padding: "12px 14px",
                border: "1px solid var(--border-soft)",
                borderRadius: 6,
                background: "var(--bg-alt)",
              }}
            >
              {s.bullets.map((b) => (
                <div
                  key={b}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 8,
                    fontSize: 12.5,
                    color: "var(--slate)",
                  }}
                >
                  <span style={{ color: s.tone.ink, display: "inline-flex" }}>
                    <Check size={13} />
                  </span>
                  {b}
                </div>
              ))}
            </div>

            <div
              style={{
                borderTop: "1px solid var(--border-soft)",
                paddingTop: 14,
                display: "flex",
                alignItems: "center",
                gap: 10,
                flexWrap: "wrap",
              }}
            >
              <span
                style={{
                  fontSize: 11,
                  color: "var(--muted)",
                  textTransform: "uppercase",
                  letterSpacing: "0.06em",
                  fontWeight: 500,
                }}
              >
                Sample
              </span>
              <span className="mono" style={{ fontSize: 12, color: "var(--ink)" }}>{s.sampleName}</span>
              <span className="mono" style={{ fontSize: 11, color: "var(--muted)" }}>{s.size}</span>
              <Link to={tryTo} className="btn btn-ghost btn-sm" style={{ marginLeft: "auto" }}>
                Try {s.name} <ArrowRight size={12} />
              </Link>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

// ── Files preview ─────────────────────────────────────────────────────────────

function SkillsFiles() {
  return (
    <section style={{ borderTop: "1px solid var(--border)", background: "var(--bg-alt)" }}>
      <div
        className="skills-files-grid"
        style={{ maxWidth: SECTION_MAX, margin: "0 auto", padding: "80px 32px", gap: 48 }}
      >
        <div>
          <span className="kicker">Files dashboard</span>
          <h2
            style={{
              fontSize: 40,
              fontWeight: 500,
              letterSpacing: "-0.03em",
              lineHeight: 1.05,
              margin: "12px 0 22px",
              color: "var(--ink)",
            }}
          >
            Every generated file, <span className="serif-i">in one place</span>.
          </h2>
          <p
            style={{
              fontSize: 15,
              color: "var(--slate)",
              lineHeight: 1.6,
              margin: "0 0 22px",
              maxWidth: 460,
            }}
          >
            Each <InlineMono>execute</InlineMono> call writes to the console's Files view. Filter
            by skill, by agent, by run. Re-download an expired URL or delete a file you didn't mean
            to keep — same auth, same tenant isolation as the rest of the product.
          </p>
          <ul
            style={{
              listStyle: "none",
              padding: 0,
              margin: "0 0 28px",
              display: "flex",
              flexDirection: "column",
              gap: 10,
            }}
          >
            {[
              "Signed URLs expire after 15 minutes — re-issue from the dashboard.",
              "Filter by skill, agent, API key, or date range.",
              "Per-tenant retention policy: keep, expire, or auto-delete.",
              "Full audit trail: who ran what, when, and what came out.",
            ].map((x) => (
              <li
                key={x}
                style={{
                  display: "flex",
                  alignItems: "flex-start",
                  gap: 10,
                  fontSize: 13.5,
                  color: "var(--slate)",
                }}
              >
                <span style={{ color: "var(--accent)", marginTop: 1, display: "inline-flex" }}>
                  <Check size={14} />
                </span>
                {x}
              </li>
            ))}
          </ul>
          <Link to="/files" className="btn btn-primary">
            Open Files in console <ArrowRight size={14} />
          </Link>
        </div>

        <FilesMock />
      </div>
    </section>
  );
}

function FilesMock() {
  return (
    <div
      className="card"
      style={{ overflow: "hidden", alignSelf: "start", background: "var(--surface)" }}
    >
      <div
        style={{
          padding: "12px 14px",
          borderBottom: "1px solid var(--border)",
          background: "var(--surface-2)",
          display: "flex",
          alignItems: "center",
          gap: 8,
        }}
      >
        <span className="mono" style={{ fontSize: 12, color: "var(--muted)" }}>
          app.harnex.dev/files
        </span>
        <span
          style={{
            marginLeft: "auto",
            display: "inline-flex",
            alignItems: "center",
            gap: 4,
            fontSize: 11,
            color: "var(--green)",
          }}
        >
          <span style={{ width: 6, height: 6, borderRadius: 999, background: "var(--green)" }} />
          live
        </span>
      </div>

      <div
        style={{
          padding: "12px 16px",
          borderBottom: "1px solid var(--border)",
          display: "flex",
          alignItems: "center",
          gap: 8,
          flexWrap: "wrap",
        }}
      >
        <span
          style={{
            fontSize: 11,
            color: "var(--muted)",
            textTransform: "uppercase",
            letterSpacing: "0.06em",
            fontWeight: 500,
          }}
        >
          Filter
        </span>
        <button
          style={{
            padding: "3px 8px",
            borderRadius: 4,
            border: "1px solid var(--ink)",
            background: "var(--ink)",
            color: "var(--bg)",
            fontSize: 11.5,
            cursor: "pointer",
            fontWeight: 500,
          }}
        >
          All · {FILES_PREVIEW.length}
        </button>
        {SKILLS.map((s) => (
          <button
            key={s.id}
            style={{
              padding: "3px 8px",
              borderRadius: 4,
              border: "1px solid var(--border)",
              background: "var(--surface)",
              color: "var(--slate)",
              fontSize: 11.5,
              cursor: "pointer",
              display: "inline-flex",
              alignItems: "center",
              gap: 5,
            }}
          >
            <span style={{ width: 8, height: 8, borderRadius: 2, background: s.tone.ink }} />
            {s.ext}
          </button>
        ))}
        <span
          style={{
            marginLeft: "auto",
            display: "inline-flex",
            alignItems: "center",
            gap: 6,
            fontSize: 11.5,
            color: "var(--muted)",
          }}
        >
          <Search size={12} />
          <span className="mono">search files…</span>
        </span>
      </div>

      <div className="table-scroll">
        <table className="tbl">
          <thead>
            <tr>
              <th>File</th>
              <th>Skill</th>
              <th>Size</th>
              <th>Created</th>
              <th>By</th>
              <th style={{ textAlign: "right" }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {FILES_PREVIEW.map((f) => (
              <tr key={f.name} className="row-hover">
                <td>
                  <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                    <SkillGlyph skill={f.skill} size={26} />
                    <span className="mono" style={{ fontSize: 12, color: "var(--ink)" }}>{f.name}</span>
                  </div>
                </td>
                <td className="mono" style={{ fontSize: 11.5, color: "var(--muted)" }}>
                  skills/{f.skill.id}
                </td>
                <td className="mono" style={{ fontSize: 11.5, color: "var(--muted)" }}>{f.size}</td>
                <td style={{ fontSize: 12, color: "var(--slate)" }}>{f.when}</td>
                <td className="mono" style={{ fontSize: 11.5, color: "var(--muted)" }}>{f.by}</td>
                <td style={{ textAlign: "right" }}>
                  <span style={{ display: "inline-flex", gap: 4, color: "var(--muted)" }}>
                    <button
                      title="Re-issue URL"
                      style={{ background: "none", border: "none", padding: 4, cursor: "pointer", color: "inherit" }}
                    >
                      <RefreshCw size={13} />
                    </button>
                    <button
                      title="Copy link"
                      style={{ background: "none", border: "none", padding: 4, cursor: "pointer", color: "inherit" }}
                    >
                      <Copy size={13} />
                    </button>
                    <button
                      title="Delete"
                      style={{ background: "none", border: "none", padding: 4, cursor: "pointer", color: "inherit" }}
                    >
                      <Trash2 size={13} />
                    </button>
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ── Callout ───────────────────────────────────────────────────────────────────

function SkillsCallout({ isAuthed }: { isAuthed: boolean }) {
  const startTo = isAuthed ? "/dashboard" : "/onboarding";
  return (
    <section style={SECTION_PAD}>
      <div
        className="card skills-callout"
        style={{ padding: "44px 48px", display: "flex", alignItems: "center", gap: 36, background: "var(--surface)" }}
      >
        <div style={{ flex: 1, minWidth: 0 }}>
          <span className="kicker">Ship documents</span>
          <h2
            style={{
              fontSize: 32,
              fontWeight: 500,
              letterSpacing: "-0.03em",
              lineHeight: 1.1,
              margin: "10px 0 12px",
              color: "var(--ink)",
            }}
          >
            Connect an API. Run a skill. <span className="serif-i">Hand back a file.</span>
          </h2>
          <p
            style={{
              fontSize: 14.5,
              color: "var(--slate)",
              margin: 0,
              lineHeight: 1.55,
              maxWidth: 640,
            }}
          >
            Skills are free on every plan, including Hobby. Usage rolls into the same execution
            quota as search and execute.
          </p>
        </div>
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          <a
            className="btn btn-ghost btn-lg"
            href={HARNEX_REPO_README}
            target="_blank"
            rel="noopener noreferrer"
          >
            <BookOpen size={14} /> View docs
          </a>
          <Link to={startTo} className="btn btn-accent btn-lg">
            Get started <ArrowRight size={14} />
          </Link>
        </div>
      </div>
    </section>
  );
}
