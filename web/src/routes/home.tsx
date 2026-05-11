import { Link, createFileRoute } from "@tanstack/react-router";
import type { ReactNode } from "react";
import { Moon, Sun } from "lucide-react";

import { useAuth } from "@/lib/auth";
import { useTheme } from "@/lib/theme";

export const Route = createFileRoute("/home")({
  component: MarketingPage,
});

// ── Logo ─────────────────────────────────────────────────────────────────────

function HarnexLogo({
  size = 24,
  accent = "var(--accent)",
  ink = "var(--ink)",
  showWordmark = true,
}: {
  size?: number;
  accent?: string;
  ink?: string;
  showWordmark?: boolean;
}) {
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 8 }}>
      <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-label="Harnex">
        <path d="M5 4 H3 V20 H5" stroke={ink} strokeWidth="2" strokeLinecap="square" fill="none" />
        <path d="M19 4 H21 V20 H19" stroke={ink} strokeWidth="2" strokeLinecap="square" fill="none" />
        <rect x="7" y="11" width="10" height="2" fill={accent} />
        <circle cx="8" cy="12" r="1.6" fill={ink} />
        <circle cx="16" cy="12" r="1.6" fill={ink} />
      </svg>
      {showWordmark && (
        <span
          style={{
            fontFamily: "var(--font-sans)",
            fontWeight: 600,
            fontSize: size * 0.72,
            letterSpacing: "-0.02em",
            color: ink,
          }}
        >
          Harnex
        </span>
      )}
    </span>
  );
}

// ── Connector marks ───────────────────────────────────────────────────────────

function Mk({ children }: { children: ReactNode }) {
  return (
    <svg width={22} height={22} viewBox="0 0 24 24" fill="none" style={{ display: "block" }}>
      {children}
    </svg>
  );
}

const C = "currentColor";

const MARKS: Record<string, ReactNode> = {
  GitHub: <Mk><circle cx="12" cy="12" r="9" fill={C}/><path d="M12 6.5c-2.7 0-5 2.2-5 4.9 0 2.2 1.4 4 3.4 4.7.2 0 .3-.1.3-.2v-.9c-1.4.3-1.7-.6-1.7-.6-.2-.6-.5-.7-.5-.7-.5-.3.04-.3.04-.3.5 0 .8.5.8.5.5.8 1.2.6 1.5.4 0-.4.2-.6.4-.8-1.1-.1-2.3-.5-2.3-2.4 0-.5.2-1 .5-1.3-.05-.1-.2-.6.05-1.3 0 0 .4-.1 1.4.5.4-.1.8-.2 1.3-.2.4 0 .9.05 1.3.2 1-.7 1.4-.5 1.4-.5.3.7.1 1.2.05 1.3.3.3.5.8.5 1.3 0 1.9-1.2 2.3-2.3 2.4.2.2.4.5.4 1v1.5c0 .1.1.2.3.2C15.6 15.4 17 13.6 17 11.4c0-2.7-2.3-4.9-5-4.9z" fill="#fff"/></Mk>,
  GitLab: <Mk><path d="M12 21 3 13l1.5-5h2L8.5 13h7L17.5 8h2L21 13z" fill={C}/></Mk>,
  Bitbucket: <Mk><path d="M4 5h16l-2.5 14h-11z" fill={C}/><rect x="10" y="9.5" width="4" height="5" fill="#fff"/></Mk>,
  Jenkins: <Mk><circle cx="12" cy="10" r="4" fill={C}/><path d="M9 14h6l1 6H8z" fill={C}/></Mk>,
  CircleCI: <Mk><circle cx="12" cy="12" r="8" stroke={C} strokeWidth="1.5" fill="none"/><circle cx="12" cy="12" r="3" fill={C}/></Mk>,
  ArgoCD: <Mk><circle cx="12" cy="12" r="7" stroke={C} strokeWidth="1.5" fill="none"/><circle cx="12" cy="12" r="2.5" fill={C}/><path d="M12 5v3M12 16v3M5 12h3M16 12h3" stroke={C} strokeWidth="1.5"/></Mk>,
  Jira: <Mk><path d="M12 4 L20 12 L16 16 L12 12 L8 16 L4 12 z" fill={C}/></Mk>,
  Linear: <Mk><circle cx="12" cy="12" r="8" stroke={C} strokeWidth="1.5" fill="none"/><path d="M6 12 L18 12 M6 8 L18 8 M6 16 L18 16" stroke={C} strokeWidth="1.5"/></Mk>,
  Notion: <Mk><rect x="5" y="4" width="14" height="16" rx="1" fill={C}/><path d="M9 8 L9 16 M9 8 L15 14 L15 8" stroke="#fff" strokeWidth="1.5" fill="none"/></Mk>,
  DataDog: <Mk><path d="M5 18 C7 14 10 12 14 12 L19 8 L18 14 L14 16 C12 17 9 18 5 18z" fill={C}/></Mk>,
  Grafana: <Mk><circle cx="12" cy="12" r="3" fill={C}/><path d="M12 3 v3 M12 18 v3 M3 12 h3 M18 12 h3 M5 5 l2 2 M17 17 l2 2 M5 19 l2 -2 M17 7 l2 -2" stroke={C} strokeWidth="1.5"/></Mk>,
  Prometheus: <Mk><circle cx="12" cy="12" r="7" fill={C}/><path d="M9 9 L15 9 M8 12 L16 12" stroke="#fff" strokeWidth="1.5"/><circle cx="12" cy="16" r="1.5" fill="#fff"/></Mk>,
  Sentry: <Mk><path d="M12 4 L20 18 H15 A3 3 0 0 0 9 18 L12 12 L15 17 L17 17 L12 7 L7 17 H4 z" fill={C}/></Mk>,
  PagerDuty: <Mk><rect x="6" y="4" width="8" height="12" fill={C}/><rect x="6" y="16" width="3" height="4" fill={C}/></Mk>,
  AWS: <Mk><path d="M4 14 C7 17 17 17 20 14" stroke={C} strokeWidth="1.8" fill="none"/><path d="M5 9 H8 V12 H5z M10 9 H13 V12 H10z M15 9 H18 V12 H15z" fill={C}/></Mk>,
  GCP: <Mk><circle cx="12" cy="12" r="7" fill="none" stroke={C} strokeWidth="1.5"/><path d="M9 12 L11 14 L15 10" stroke={C} strokeWidth="1.8" fill="none"/></Mk>,
  Azure: <Mk><path d="M11 4 L20 20 H10 L13 14 L8 20 H4 z" fill={C}/></Mk>,
  Cloudflare: <Mk><path d="M5 16 C5 12 8 11 11 12 C11 9 14 8 17 10 C20 10 21 14 19 16 z" fill={C}/></Mk>,
  Vercel: <Mk><path d="M12 5 L21 19 H3 z" fill={C}/></Mk>,
  Docker: <Mk><rect x="5" y="11" width="3" height="3" fill={C}/><rect x="9" y="11" width="3" height="3" fill={C}/><rect x="13" y="11" width="3" height="3" fill={C}/><rect x="9" y="7" width="3" height="3" fill={C}/><path d="M4 14 C8 18 16 18 19 14 L20 13" stroke={C} strokeWidth="1.5" fill="none"/></Mk>,
  Kubernetes: <Mk><path d="M12 4 L19 8 L17 16 L12 20 L7 16 L5 8 z" fill="none" stroke={C} strokeWidth="1.5"/><circle cx="12" cy="12" r="2" fill={C}/></Mk>,
  Terraform: <Mk><path d="M5 5 L11 8 V14 L5 11 z M11 8 L17 5 V11 L11 14 z M11 14 L17 11 V17 L11 20 z M5 12 L11 15 V20 L5 17 z" fill={C}/></Mk>,
  Postgres: <Mk><ellipse cx="12" cy="8" rx="7" ry="2.5" fill={C}/><path d="M5 8 V16 C5 17.5 8 18.5 12 18.5 C16 18.5 19 17.5 19 16 V8" stroke={C} strokeWidth="1.5" fill="none"/><ellipse cx="12" cy="12" rx="7" ry="2.5" fill="none" stroke={C} strokeWidth="1.5"/></Mk>,
  MongoDB: <Mk><path d="M12 4 C9 8 9 16 12 20 C15 16 15 8 12 4 z" fill={C}/><path d="M12 4 V20" stroke="#fff" strokeWidth="1"/></Mk>,
  Redis: <Mk><ellipse cx="12" cy="7" rx="7" ry="2" fill={C}/><path d="M5 7 V11 C5 12 8 13 12 13 C16 13 19 12 19 11 V7" stroke={C} strokeWidth="1.5" fill="none"/><path d="M5 13 V17 C5 18 8 19 12 19 C16 19 19 18 19 17 V13" stroke={C} strokeWidth="1.5" fill="none"/></Mk>,
  Snowflake: <Mk><path d="M12 4 V20 M4 12 H20 M6 6 L18 18 M18 6 L6 18" stroke={C} strokeWidth="1.5"/></Mk>,
  Supabase: <Mk><path d="M12 4 L4 14 H10 L8 20 L20 10 H14 L16 4 z" fill={C}/></Mk>,
  Slack: <Mk><rect x="4" y="10" width="6" height="2" rx="1" fill={C}/><rect x="14" y="12" width="6" height="2" rx="1" fill={C}/><rect x="10" y="4" width="2" height="6" rx="1" fill={C}/><rect x="12" y="14" width="2" height="6" rx="1" fill={C}/></Mk>,
  Discord: <Mk><path d="M5 7 C8 5 16 5 19 7 L20 16 C18 18 14 19 14 19 L13 17 C12 17 12 17 11 17 L10 19 C10 19 6 18 4 16 z" fill={C}/><circle cx="9.5" cy="13" r="1.2" fill="#fff"/><circle cx="14.5" cy="13" r="1.2" fill="#fff"/></Mk>,
  Stripe: <Mk><path d="M16 7 H8 C6 7 6 10 8 10 L14 12 C16 12.5 16 16 14 16 H7" stroke={C} strokeWidth="2" fill="none"/></Mk>,
  HubSpot: <Mk><circle cx="14" cy="14" r="4" stroke={C} strokeWidth="1.5" fill="none"/><circle cx="14" cy="6" r="1.8" fill={C}/><path d="M14 8 V10 M11 11 L8 14 M8 14 V18" stroke={C} strokeWidth="1.5"/></Mk>,
  Salesforce: <Mk><ellipse cx="12" cy="13" rx="7" ry="4" fill={C}/><circle cx="9" cy="11" r="2.5" fill={C}/><circle cx="15" cy="11" r="2" fill={C}/></Mk>,
  Zendesk: <Mk><path d="M4 6 L12 6 L4 16 z M12 18 C12 14 16 10 20 10 L20 18 z" fill={C}/></Mk>,
  Intercom: <Mk><rect x="5" y="5" width="14" height="14" rx="2" fill={C}/><path d="M8 9 V14 M11 9 V15 M14 9 V15 M17 9 V14" stroke="#fff" strokeWidth="1.2"/></Mk>,
  OpenAI: <Mk><circle cx="12" cy="12" r="8" stroke={C} strokeWidth="1.5" fill="none"/><path d="M12 6 L17 9 L17 15 L12 18 L7 15 L7 9 z" stroke={C} strokeWidth="1.2" fill="none"/></Mk>,
  Anthropic: <Mk><path d="M9 5 L5 19 H8 L9 16 H13 L14 19 H17 L13 5 z M10 13 L11 9 L12 13 z" fill={C}/></Mk>,
  Twilio: <Mk><circle cx="12" cy="12" r="8" stroke={C} strokeWidth="1.5" fill="none"/><circle cx="9" cy="9" r="1.5" fill={C}/><circle cx="15" cy="9" r="1.5" fill={C}/><circle cx="9" cy="15" r="1.5" fill={C}/><circle cx="15" cy="15" r="1.5" fill={C}/></Mk>,
  Airtable: <Mk><path d="M4 8 L12 12 L20 8 L12 4 z M4 13 L12 17 L20 13 M4 17 L12 21 L20 17" stroke={C} strokeWidth="1.5" fill="none"/></Mk>,
  Elasticsearch: <Mk><path d="M4 6 H20 V10 H4 z M8 11 H20 V15 H8 z M12 16 H20 V20 H12 z" fill={C}/></Mk>,
  Pinecone: <Mk><path d="M12 4 L8 8 L12 6 L16 8 z M12 7 L9 11 L12 9 L15 11 z M12 10 L10 14 L12 12 L14 14 z M11 14 L13 14 L12 20 z" fill={C}/></Mk>,
};

const CONNECTOR_LIST = Object.keys(MARKS);

function ConnectorCell({ name }: { name: string }) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 10,
        height: 52,
        minWidth: 160,
        padding: "0 16px",
        border: "1px solid var(--border)",
        borderRadius: 8,
        background: "var(--surface)",
        color: "var(--slate)",
        flexShrink: 0,
        marginRight: 8,
      }}
    >
      <span style={{ color: "var(--ink)", display: "inline-flex" }}>{MARKS[name]}</span>
      <span style={{ fontSize: 13, fontWeight: 500, color: "var(--ink)" }}>{name}</span>
    </div>
  );
}

// ── Data ─────────────────────────────────────────────────────────────────────

const PROBLEM_STATS = [
  {
    apis: 5,
    tools: 5,
    label: "Barely manageable",
    color: "var(--green)",
    barPct: 10,
  },
  {
    apis: 15,
    tools: 15,
    label: "Context pressure starts",
    color: "var(--amber)",
    barPct: 30,
  },
  {
    apis: 30,
    tools: 30,
    label: "Reliable tool selection collapses",
    color: "var(--red)",
    barPct: 62,
  },
  {
    apis: 50,
    tools: 50,
    label: "Agent is effectively unusable",
    color: "var(--red)",
    barPct: 100,
  },
];

const COMPARISON = [
  {
    side: "before" as const,
    label: "Every other MCP approach",
    accent: "var(--red)",
    accentSoft: "var(--red-soft)",
    accentBorder: "var(--red-border)",
    points: [
      "1 API = 1 MCP server = N new tools exposed",
      "50 APIs means 50+ tools eating your context window",
      "Tool selection hallucinations compound with every addition",
      "Agents forget earlier tools as the list grows past ~15",
      "Each integration needs bespoke auth wiring",
      "Adoption collapses well before you hit 20 integrations",
    ],
  },
  {
    side: "after" as const,
    label: "Harnex",
    accent: "var(--accent)",
    accentSoft: "var(--accent-soft)",
    accentBorder: "var(--accent-border)",
    points: [
      "50 APIs. Still exactly 2 MCP tools: search and execute",
      "Context window never changes regardless of API count",
      "Semantic search eliminates selection hallucinations",
      "Deterministic execute — no LLM in the call path",
      "Auth goes to the vault at connect time, never touched again",
      "Scales to unlimited integrations with zero agent degradation",
    ],
  },
];

const FEATURES = [
  {
    icon: "2",
    title: "Two tools. Always.",
    desc: "Connect 50 APIs. Your agent still sees exactly search and execute. Context window stays clean by design, not by luck — no matter how many APIs you add.",
  },
  {
    icon: "~",
    title: "Semantic op search",
    desc: "Every API operation is embedded and indexed. Your agent searches in natural language; Harnex returns ranked operations with cosine scores — not docs, not hallucinations.",
  },
  {
    icon: "→",
    title: "Deterministic execute",
    desc: "No LLM in the execution path. Execute binds parameters to the OpenAPI spec, resolves auth from the vault, and fires the HTTP request. Pure and auditable.",
  },
  {
    icon: "⌿",
    title: "Vault-first secrets",
    desc: "API keys and OAuth tokens go to Infisical at connection time. Postgres holds zero plaintext credentials — only auth flow type and key references.",
  },
  {
    icon: "?",
    title: "Clarification signal",
    desc: "When a search query spans multiple APIs, Harnex returns clarification_needed so your agent can ask which platform was meant — instead of guessing wrong.",
  },
  {
    icon: "T",
    title: "Tenant-isolated",
    desc: "Each tenant gets a separate vector index, credential namespace, and API quota. Multi-tenant by design, not bolted on as an afterthought.",
  },
];

const STEPS = [
  {
    n: "01",
    title: "Connect an API",
    desc: "Point at a built-in connector, OpenAPI URL, uploaded spec, or bare URL. Auth secrets go directly to the vault — never your DB, never plaintext.",
  },
  {
    n: "02",
    title: "Index operations",
    desc: "Every operation is extracted, semantically tagged, embedded, and upserted into your tenant's vector index. One chunk per operation. No manual tagging.",
  },
  {
    n: "03",
    title: "Point your agent",
    desc: "Add your Harnex MCP URL to Claude Code, Cursor, or Windsurf. Exactly two tools appear: search and execute. That is the complete surface. Always.",
  },
  {
    n: "04",
    title: "Search → execute",
    desc: "Agent calls search, gets ranked hits with cosine scores. Calls execute with connection_id + operation_id + params. Harnex does the rest. No hallucination path.",
  },
];

const USE_CASES = [
  {
    title: "Claude Code & Cursor",
    badge: "Code Agents",
    desc: "Your coding agent shouldn't need 40 tools to talk to your stack. Give it search and execute, and let it find what it needs.",
    items: ["Trigger CI/CD pipelines from a chat message", "Open PRs and review diffs on demand", "Query metrics and alerts inline without leaving the editor"],
  },
  {
    title: "Customer Support",
    badge: "Support Agents",
    desc: "A support bot that hallucinates API calls isn't a support bot. Harnex makes every execution deterministic and auditable.",
    items: ["Look up orders and subscriptions without custom tools", "Issue refunds through Stripe — confirmed, not hallucinated", "Update CRM records in-line with full audit trail"],
  },
  {
    title: "Platform Teams",
    badge: "Multi-tenant",
    desc: "Ship one MCP server to every customer. Harnex handles tenant isolation, auth namespacing, and per-tenant quota enforcement.",
    items: ["Isolated vector index and credentials per customer", "Per-tenant API quotas and key management", "Execution audit log across the entire fleet"],
  },
];

const PRICING = [
  {
    name: "Hobby",
    price: "Free",
    period: "",
    features: ["1 tenant", "500 executions / mo", "5 connections", "Community support"],
    cta: "Get started",
    accent: false,
  },
  {
    name: "Team",
    price: "$99",
    period: "/month",
    features: ["Unlimited tenants", "50,000 executions / mo", "50 connections", "Priority support", "SSO / OIDC"],
    cta: "Start free trial",
    accent: true,
  },
  {
    name: "Enterprise",
    price: "Custom",
    period: "",
    features: ["Unlimited everything", "On-prem deployment", "Custom SLA", "Dedicated support"],
    cta: "Contact us",
    accent: false,
  },
];

// ── Page ─────────────────────────────────────────────────────────────────────

function MarketingPage() {
  const auth = useAuth();
  const isAuthed = auth.status === "authenticated";
  const { theme, toggle: toggleTheme } = useTheme();

  const row1 = [...CONNECTOR_LIST, ...CONNECTOR_LIST, ...CONNECTOR_LIST];
  const mid = Math.floor(CONNECTOR_LIST.length / 2);
  const row2 = [
    ...CONNECTOR_LIST.slice(mid),
    ...CONNECTOR_LIST,
    ...CONNECTOR_LIST,
    ...CONNECTOR_LIST.slice(0, mid),
  ];

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
      {/* ── Header ── */}
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
            maxWidth: 1120,
            margin: "0 auto",
            padding: "0 32px",
            height: 52,
            display: "flex",
            alignItems: "center",
            gap: 24,
          }}
        >
          <HarnexLogo size={22} />
          <nav className="marketing-nav">
            {["The Problem", "How it works", "Use cases", "Security", "Pricing"].map((l) => (
              <a
                key={l}
                href={`#${l.toLowerCase().replace(/ /g, "-")}`}
                style={{
                  fontSize: 13.5,
                  fontWeight: 500,
                  color: "var(--slate)",
                  padding: "5px 10px",
                  borderRadius: "var(--r-sm)",
                  transition: "color 80ms",
                  textDecoration: "none",
                }}
                onMouseEnter={(e) => ((e.target as HTMLElement).style.color = "var(--ink)")}
                onMouseLeave={(e) => ((e.target as HTMLElement).style.color = "var(--slate)")}
              >
                {l}
              </a>
            ))}
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
              <Link to="/dashboard">
                <button className="btn btn-ghost btn-sm">Console →</button>
              </Link>
            ) : (
              <>
                <Link to="/onboarding">
                  <button className="btn btn-accent btn-sm">Get started →</button>
                </Link>
              </>
            )}
          </div>
        </div>
      </header>

      {/* ── Hero ── */}
      <section
        id="product"
        className="marketing-section marketing-hero"
        style={{
          maxWidth: 1120,
          margin: "0 auto",
          padding: "80px 32px 64px",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          textAlign: "center",
        }}
      >
        {/* Badge pill — warning tone */}
        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 8,
            border: "1px solid var(--red-border)",
            borderRadius: 999,
            padding: "4px 14px 4px 4px",
            marginBottom: 28,
            background: "var(--red-soft)",
          }}
        >
          <span className="badge badge-red badge-mono" style={{ height: 20, fontSize: 10 }}>BROKEN</span>
          <span style={{ fontSize: 12.5, color: "var(--red-ink)", fontWeight: 500 }}>
            The MCP tool explosion is collapsing agent reliability. There's one exit.
          </span>
        </div>

        {/* H1 */}
        <h1
          style={{
            fontSize: "clamp(48px, 8vw, 80px)",
            fontWeight: 600,
            letterSpacing: "-0.04em",
            lineHeight: 1.02,
            margin: "0 0 22px",
            color: "var(--ink)",
          }}
        >
          MCPs are{" "}
          <span className="serif-i" style={{ fontSize: "1.05em", color: "var(--red)" }}>
            broken.
          </span>
          <br />
          We{" "}
          <span className="serif-i" style={{ fontSize: "1.05em", color: "var(--accent)" }}>
            fixed it.
          </span>
        </h1>

        <p
          style={{
            fontSize: 17,
            color: "var(--slate)",
            maxWidth: 600,
            margin: "0 0 36px",
            lineHeight: 1.65,
          }}
        >
          The last MCP you'll ever need.
        </p>

        <div className="marketing-hero-actions">
          {isAuthed ? (
            <Link to="/dashboard">
              <button className="btn btn-accent btn-lg">Open console →</button>
            </Link>
          ) : (
            <Link to="/onboarding">
              <button className="btn btn-accent btn-lg">
                Escape the tool explosion →
              </button>
            </Link>
          )}
          <a href="#the-problem" className="btn btn-ghost btn-lg" style={{ textDecoration: "none" }}>
            See why it's broken
          </a>
        </div>

        <div
          className="marketing-command"
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 10,
            background: "var(--surface-2)",
            border: "1px solid var(--border)",
            borderRadius: 8,
            padding: "8px 16px",
            fontFamily: "var(--font-mono)",
            fontSize: 13,
            color: "var(--slate)",
            marginBottom: 48,
          }}
        >
          <span style={{ color: "var(--muted)" }}>$</span>
          <span>npx harnex-mcp --url https://api.harnex.dev --key hx_…</span>
        </div>

        {/* Console preview */}
        <div
          className="marketing-console"
          style={{
            borderRadius: "var(--r-xl)",
            border: "1px solid var(--border)",
            overflow: "hidden",
            boxShadow: "var(--shadow-lg)",
            background: "var(--surface-2)",
            textAlign: "left",
          }}
        >
          {/* Window chrome */}
          <div
            style={{
              padding: "10px 14px",
              borderBottom: "1px solid var(--border)",
              display: "flex",
              alignItems: "center",
              gap: 6,
              background: "var(--surface)",
            }}
          >
            {["#DC2626", "#D97706", "#16A34A"].map((c) => (
              <span key={c} style={{ width: 10, height: 10, borderRadius: "50%", background: c, opacity: 0.8 }} />
            ))}
            <span style={{ marginLeft: 8, fontSize: 11, color: "var(--muted)" }}>
              app.harnex.dev — 2 tools, 47 APIs connected
            </span>
          </div>
          {/* 3-col console mockup */}
          <div className="marketing-console-grid">
            {/* Sidebar */}
            <div
              className="marketing-console-sidebar"
              style={{
                borderRight: "1px solid var(--border)",
                padding: "14px 10px",
                display: "flex",
                flexDirection: "column",
                gap: 2,
              }}
            >
              <div style={{ fontSize: 10, color: "var(--muted)", fontWeight: 600, padding: "0 6px 8px", letterSpacing: "0.06em" }}>
                YOUR APIS
              </div>
              {[
                { name: "GitHub", status: "ready" },
                { name: "Jenkins", status: "ready" },
                { name: "DataDog", status: "indexing" },
                { name: "Stripe", status: "ready" },
              ].map((c) => (
                <div
                  key={c.name}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 7,
                    padding: "5px 6px",
                    borderRadius: 4,
                    background: c.name === "GitHub" ? "var(--surface-2)" : "transparent",
                  }}
                >
                  <span
                    style={{
                      width: 6,
                      height: 6,
                      borderRadius: "50%",
                      background: c.status === "ready" ? "var(--green)" : "var(--amber)",
                      flexShrink: 0,
                    }}
                  />
                  <span style={{ fontSize: 12, color: "var(--ink)", fontWeight: c.name === "GitHub" ? 500 : 400 }}>
                    {c.name}
                  </span>
                </div>
              ))}
            </div>
            {/* Search panel */}
            <div className="marketing-console-search" style={{ borderRight: "1px solid var(--border)", padding: 16 }}>
              <div style={{ display: "flex", gap: 8, marginBottom: 14 }}>
                <input
                  className="input"
                  style={{ flex: 1, fontSize: 12.5 }}
                  defaultValue="list open PRs assigned to me in review"
                  readOnly
                />
                <button className="btn btn-accent" style={{ flexShrink: 0, fontSize: 12 }}>Search</button>
              </div>
              {[
                { method: "GET", path: "/repos/{owner}/{repo}/pulls", score: "0.94", summary: "List pull requests" },
                { method: "GET", path: "/user/issues", score: "0.87", summary: "List issues for user" },
                { method: "GET", path: "/repos/{owner}/{repo}/issues", score: "0.81", summary: "List repo issues" },
              ].map((h) => (
                <div
                  key={h.path}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 8,
                    padding: "7px 0",
                    borderBottom: "1px solid var(--border-soft)",
                  }}
                >
                  <span className={`method method-${h.method.toLowerCase()}`}>{h.method}</span>
                  <span style={{ flex: 1 }}>
                    <div className="mono" style={{ fontSize: 11, color: "var(--ink)" }}>{h.path}</div>
                    <div style={{ fontSize: 10.5, color: "var(--muted)", marginTop: 1 }}>{h.summary}</div>
                  </span>
                  <span className="mono" style={{ fontSize: 11, color: "var(--muted)", flexShrink: 0 }}>{h.score}</span>
                </div>
              ))}
            </div>
            {/* Execution log */}
            <div style={{ padding: 16 }}>
              <div style={{ fontSize: 11, color: "var(--muted)", fontWeight: 600, marginBottom: 10, letterSpacing: "0.05em" }}>
                execute() → response
              </div>
              <div
                style={{
                  background: "var(--surface-2)",
                  border: "1px solid var(--border)",
                  borderRadius: 6,
                  padding: "10px 12px",
                  fontFamily: "var(--font-mono)",
                  fontSize: 11.5,
                  color: "var(--slate)",
                  lineHeight: 1.7,
                }}
              >
                <div><span style={{ color: "var(--muted)" }}>operation_id:</span> <span style={{ color: "var(--ink)" }}>listPullRequests</span></div>
                <div><span style={{ color: "var(--muted)" }}>status:</span> <span style={{ color: "var(--green)" }}>"success"</span></div>
                <div><span style={{ color: "var(--muted)" }}>http_status:</span> 200</div>
                <div><span style={{ color: "var(--muted)" }}>duration_ms:</span> 312</div>
                <div><span style={{ color: "var(--muted)" }}>body:</span> {"{"} items: 7 {"}"}</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── The MCP Problem ── */}
      <section
        id="the-problem"
        style={{
          background: "var(--surface-2)",
          borderTop: "1px solid var(--border)",
          borderBottom: "1px solid var(--border)",
        }}
      >
        <div className="marketing-section" style={{ maxWidth: 1120, margin: "0 auto", padding: "80px 32px" }}>
          <div className="kicker" style={{ textAlign: "center", marginBottom: 12 }}>The real problem</div>
          <h2
            style={{
              fontSize: 36,
              fontWeight: 600,
              letterSpacing: "-0.03em",
              textAlign: "center",
              margin: "0 0 16px",
              color: "var(--ink)",
            }}
          >
            N APIs ={" "}
            <span className="serif-i" style={{ color: "var(--red)" }}>N tools</span>
            {" "}= agent collapse
          </h2>
          <p
            style={{
              textAlign: "center",
              fontSize: 15,
              color: "var(--slate)",
              maxWidth: 600,
              margin: "0 auto 48px",
              lineHeight: 1.65,
            }}
          >
            Every MCP server you add today exposes a new set of tools to your agent. LLMs degrade
            sharply when tool counts exceed single digits. This isn't a configuration problem.
            It's an architectural collapse.
          </p>

          {/* Bar chart */}
          <div style={{ maxWidth: 720, margin: "0 auto 48px", display: "flex", flexDirection: "column", gap: 20 }}>
            {PROBLEM_STATS.map((row) => (
              <div key={row.apis} style={{ display: "flex", flexDirection: "column", gap: 7 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
                  <span
                    style={{
                      fontSize: 13,
                      fontWeight: 600,
                      color: "var(--ink)",
                      fontFamily: "var(--font-mono)",
                    }}
                  >
                    {row.apis} APIs → {row.tools} MCP tools
                  </span>
                  <span style={{ fontSize: 12, color: row.color, fontWeight: 500 }}>
                    {row.label}
                  </span>
                </div>
                <div
                  style={{
                    height: 8,
                    borderRadius: 999,
                    background: "var(--border)",
                    overflow: "hidden",
                  }}
                >
                  <div
                    style={{
                      height: "100%",
                      borderRadius: 999,
                      width: `${row.barPct}%`,
                      background: row.color,
                    }}
                  />
                </div>
              </div>
            ))}
          </div>

          {/* Harnex invariant callout */}
          <div
            style={{
              maxWidth: 720,
              margin: "0 auto",
              border: "1px solid var(--accent-border)",
              background: "var(--accent-soft)",
              borderRadius: "var(--r-xl)",
              padding: "28px 36px",
              textAlign: "center",
            }}
          >
            <div
              style={{
                fontSize: 11,
                color: "var(--accent-ink)",
                fontWeight: 700,
                letterSpacing: "0.08em",
                marginBottom: 12,
                fontFamily: "var(--font-mono)",
              }}
            >
              HARNEX INVARIANT
            </div>
            <div
              style={{
                fontSize: "clamp(24px, 3vw, 34px)",
                fontWeight: 600,
                letterSpacing: "-0.03em",
                color: "var(--ink)",
                lineHeight: 1.2,
              }}
            >
              50 APIs.{" "}
              <span className="serif-i" style={{ color: "var(--accent)" }}>
                Always 2 tools.
              </span>
            </div>
            <p
              style={{
                fontSize: 14,
                color: "var(--slate)",
                margin: "14px 0 0",
                lineHeight: 1.65,
                maxWidth: 480,
                marginLeft: "auto",
                marginRight: "auto",
              }}
            >
              search and execute are universal operations, not per-service wrappers.
              The context window never changes regardless of how many APIs you connect.
            </p>
          </div>
        </div>
      </section>

      {/* ── Connector marquee ── */}
      <section
        style={{
          borderTop: "1px solid var(--border)",
          borderBottom: "1px solid var(--border)",
          padding: "12px 0 20px",
          overflow: "hidden",
          maskImage: "linear-gradient(to right, transparent 0%, black 8%, black 92%, transparent 100%)",
          WebkitMaskImage: "linear-gradient(to right, transparent 0%, black 8%, black 92%, transparent 100%)",
        }}
      >
        <div
          style={{
            textAlign: "center",
            padding: "8px 0 12px",
            fontSize: 11,
            color: "var(--muted)",
            fontWeight: 600,
            letterSpacing: "0.08em",
          }}
        >
          ALL OF THESE — STILL JUST 2 TOOLS
        </div>
        <div className="marquee-l" style={{ display: "flex", width: "max-content", gap: 0 }}>
          {row1.map((name, i) => (
            <ConnectorCell key={`l-${i}`} name={name} />
          ))}
        </div>
        <div className="marquee-r" style={{ display: "flex", width: "max-content", gap: 0, marginTop: 8 }}>
          {row2.map((name, i) => (
            <ConnectorCell key={`r-${i}`} name={name} />
          ))}
        </div>
      </section>

      {/* ── Features / The Fix ── */}
      <section id="features" style={{ maxWidth: 1120, margin: "0 auto", padding: "80px 32px" }}>
        <div className="kicker" style={{ textAlign: "center", marginBottom: 12 }}>Why it actually works</div>
        <h2
          style={{
            fontSize: 36,
            fontWeight: 600,
            letterSpacing: "-0.03em",
            textAlign: "center",
            margin: "0 0 12px",
            color: "var(--ink)",
          }}
        >
          The{" "}
          <span className="serif-i" style={{ color: "var(--accent)" }}>invariant</span>
          {" "}that makes agents reliable
        </h2>
        <p
          style={{
            textAlign: "center",
            fontSize: 15,
            color: "var(--slate)",
            maxWidth: 540,
            margin: "0 auto 48px",
            lineHeight: 1.65,
          }}
        >
          Every other approach gives your agent N tools for N APIs and hopes the LLM picks correctly.
          Harnex inverts that — search and execute are universal, not per-service wrappers.
        </p>
        <div className="responsive-grid-3" style={{ gap: 16 }}>
          {FEATURES.map((f) => (
            <div key={f.title} className="card" style={{ padding: 24 }}>
              <div
                style={{
                  width: 32,
                  height: 32,
                  borderRadius: "var(--r-md)",
                  background: "var(--accent-soft)",
                  border: "1px solid var(--accent-border)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  marginBottom: 14,
                  fontSize: 13,
                  fontWeight: 700,
                  color: "var(--accent)",
                  fontFamily: "var(--font-mono)",
                }}
              >
                {f.icon}
              </div>
              <h3 style={{ fontSize: 15, fontWeight: 600, margin: "0 0 8px", letterSpacing: "-0.02em", color: "var(--ink)" }}>{f.title}</h3>
              <p style={{ fontSize: 13.5, color: "var(--slate)", margin: 0, lineHeight: 1.65 }}>{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Before / After Comparison ── */}
      <section
        style={{
          background: "var(--surface-2)",
          borderTop: "1px solid var(--border)",
          borderBottom: "1px solid var(--border)",
        }}
      >
        <div className="marketing-section" style={{ maxWidth: 1120, margin: "0 auto", padding: "80px 32px" }}>
          <div className="kicker" style={{ textAlign: "center", marginBottom: 12 }}>The difference</div>
          <h2
            style={{
              fontSize: 36,
              fontWeight: 600,
              letterSpacing: "-0.03em",
              textAlign: "center",
              margin: "0 0 48px",
              color: "var(--ink)",
            }}
          >
            What you're escaping.{" "}
            What you're{" "}
            <span className="serif-i" style={{ color: "var(--accent)" }}>getting.</span>
          </h2>
          <div className="responsive-grid-2" style={{ gap: 16 }}>
            {COMPARISON.map((col) => (
              <div
                key={col.side}
                className="card"
                style={{
                  padding: 28,
                  border: `1px solid ${col.accentBorder}`,
                  background: col.accentSoft,
                }}
              >
                <div
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: 6,
                    marginBottom: 20,
                    padding: "4px 10px",
                    borderRadius: 999,
                    border: `1px solid ${col.accentBorder}`,
                    background: "var(--surface)",
                  }}
                >
                  <span
                    style={{
                      width: 8,
                      height: 8,
                      borderRadius: "50%",
                      background: col.accent,
                      flexShrink: 0,
                    }}
                  />
                  <span style={{ fontSize: 12, fontWeight: 600, color: "var(--ink)" }}>{col.label}</span>
                </div>
                <ul style={{ margin: 0, padding: 0, listStyle: "none", display: "flex", flexDirection: "column", gap: 12 }}>
                  {col.points.map((pt) => (
                    <li key={pt} style={{ display: "flex", gap: 10, fontSize: 13.5, color: "var(--slate)", lineHeight: 1.55 }}>
                      <span
                        style={{
                          width: 18,
                          height: 18,
                          borderRadius: "50%",
                          flexShrink: 0,
                          marginTop: 1,
                          background: col.side === "before" ? "var(--red-soft)" : "var(--green-soft)",
                          border: `1px solid ${col.side === "before" ? "var(--red-border)" : "var(--green-border)"}`,
                          display: "inline-flex",
                          alignItems: "center",
                          justifyContent: "center",
                          color: col.side === "before" ? "var(--red)" : "var(--green)",
                          fontSize: 10,
                          fontWeight: 700,
                        }}
                      >
                        {col.side === "before" ? "✕" : "✓"}
                      </span>
                      {pt}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── How it works ── */}
      <section id="how-it-works">
        <div className="marketing-section" style={{ maxWidth: 1120, margin: "0 auto", padding: "80px 32px" }}>
          <div className="kicker" style={{ textAlign: "center", marginBottom: 12 }}>Zero to two tools</div>
          <h2
            style={{
              fontSize: 36,
              fontWeight: 600,
              letterSpacing: "-0.03em",
              textAlign: "center",
              margin: "0 0 48px",
              color: "var(--ink)",
            }}
          >
            From spec to{" "}
            <span className="serif-i" style={{ color: "var(--accent)" }}>agent-ready</span>
            {" "}in minutes
          </h2>
          <div
            className="responsive-grid-4"
            style={{
              border: "1px solid var(--border)",
              borderRadius: "var(--r-lg)",
              overflow: "hidden",
              background: "var(--surface)",
            }}
          >
            {STEPS.map((s, i) => (
              <div
                key={s.n}
                style={{
                  padding: "28px 24px",
                  borderRight: i < STEPS.length - 1 ? "1px solid var(--border)" : "none",
                }}
              >
                <div
                  className="mono"
                  style={{
                    fontSize: 28,
                    fontWeight: 700,
                    letterSpacing: "-0.04em",
                    color: "var(--border-strong)",
                    marginBottom: 16,
                  }}
                >
                  {s.n}
                </div>
                <h3 style={{ fontSize: 14, fontWeight: 600, margin: "0 0 8px", color: "var(--ink)" }}>{s.title}</h3>
                <p style={{ fontSize: 13, color: "var(--slate)", margin: 0, lineHeight: 1.65 }}>{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Use cases ── */}
      <section
        id="use-cases"
        style={{
          background: "var(--surface-2)",
          borderTop: "1px solid var(--border)",
          borderBottom: "1px solid var(--border)",
        }}
      >
        <div className="marketing-section" style={{ maxWidth: 1120, margin: "0 auto", padding: "80px 32px" }}>
          <div className="kicker" style={{ textAlign: "center", marginBottom: 12 }}>Who escapes first</div>
          <h2
            style={{
              fontSize: 36,
              fontWeight: 600,
              letterSpacing: "-0.03em",
              textAlign: "center",
              margin: "0 0 12px",
              color: "var(--ink)",
            }}
          >
            Any agent. Any{" "}
            <span className="serif-i" style={{ color: "var(--accent)" }}>workflow.</span>
            {" "}Zero tool bloat.
          </h2>
          <p
            style={{
              textAlign: "center",
              fontSize: 15,
              color: "var(--slate)",
              maxWidth: 520,
              margin: "0 auto 48px",
              lineHeight: 1.65,
            }}
          >
            Teams shipping AI agents on top of real APIs. They don't have the luxury of 50 custom tools.
          </p>
          <div className="responsive-grid-3" style={{ gap: 16 }}>
            {USE_CASES.map((u) => (
              <div key={u.title} className="card" style={{ padding: 24 }}>
                <span className="badge badge-slate badge-mono" style={{ marginBottom: 10, display: "inline-block" }}>
                  {u.badge}
                </span>
                <h3 style={{ fontSize: 15, fontWeight: 600, margin: "0 0 8px", letterSpacing: "-0.02em", color: "var(--ink)" }}>
                  {u.title}
                </h3>
                <p style={{ fontSize: 13, color: "var(--muted)", margin: "0 0 14px", lineHeight: 1.6 }}>
                  {u.desc}
                </p>
                <ul style={{ margin: 0, padding: 0, listStyle: "none", display: "flex", flexDirection: "column", gap: 8 }}>
                  {u.items.map((item) => (
                    <li key={item} style={{ display: "flex", gap: 8, fontSize: 13.5, color: "var(--slate)" }}>
                      <svg
                        width={14}
                        height={14}
                        viewBox="0 0 24 24"
                        fill="none"
                        style={{ flexShrink: 0, marginTop: 2, color: "var(--accent)" }}
                      >
                        <path d="M5 13l4 4L19 7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                      </svg>
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Security ── */}
      <section id="security">
        <div
          className="marketing-section marketing-security-grid"
          style={{
            maxWidth: 1120,
            margin: "0 auto",
            padding: "80px 32px",
            display: "grid",
            gap: 56,
            alignItems: "center",
          }}
        >
          <div>
            <div className="kicker" style={{ marginBottom: 12 }}>No shortcuts in the chain</div>
            <h2 style={{ fontSize: 32, fontWeight: 600, letterSpacing: "-0.03em", margin: "0 0 16px", color: "var(--ink)" }}>
              Secrets stay in the{" "}
              <span className="serif-i" style={{ color: "var(--accent)" }}>vault</span>.
              {" "}Always.
            </h2>
            <p style={{ fontSize: 14, color: "var(--slate)", margin: "0 0 28px", lineHeight: 1.75 }}>
              API keys and OAuth tokens go to Infisical at connection time. Postgres holds zero plaintext — only the auth flow type and non-secret config. At execute time, the runner fetches the secret, builds the request, fires it, and discards the credential.
            </p>
            <ul style={{ margin: 0, padding: 0, listStyle: "none", display: "flex", flexDirection: "column", gap: 10 }}>
              {[
                "Zero plaintext secrets in Postgres",
                "Per-tenant Infisical credential namespaces",
                "PBKDF2-hashed API key verification",
                "Deterministic execute — no LLM touches your credentials",
              ].map((item) => (
                <li key={item} style={{ display: "flex", gap: 10, fontSize: 13.5, color: "var(--slate)" }}>
                  <span
                    style={{
                      width: 18,
                      height: 18,
                      borderRadius: "50%",
                      background: "var(--green-soft)",
                      border: "1px solid var(--green-border)",
                      display: "inline-flex",
                      alignItems: "center",
                      justifyContent: "center",
                      color: "var(--green)",
                      fontSize: 10,
                      flexShrink: 0,
                      marginTop: 2,
                    }}
                  >
                    ✓
                  </span>
                  {item}
                </li>
              ))}
            </ul>
          </div>
          <div className="card" style={{ padding: 24 }}>
            <div
              style={{
                fontSize: 11,
                color: "var(--muted)",
                fontWeight: 600,
                letterSpacing: "0.06em",
                marginBottom: 16,
              }}
            >
              EXECUTION FLOW
            </div>
            {[
              { from: "Agent", to: "MCP server", label: "search / execute" },
              { from: "MCP server", to: "Harnex API", label: "verified API key" },
              { from: "Harnex API", to: "Infisical", label: "fetch secret" },
              { from: "Harnex API", to: "Target API", label: "authed call" },
            ].map((step, i) => (
              <div
                key={i}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 6,
                  marginBottom: 10,
                  paddingBottom: 10,
                  borderBottom: i < 3 ? "1px solid var(--border-soft)" : "none",
                  fontFamily: "var(--font-mono)",
                  fontSize: 11,
                  minWidth: 0,
                }}
              >
                <span
                  style={{
                    background: "var(--ink)",
                    color: "var(--bg)",
                    borderRadius: 3,
                    padding: "2px 6px",
                    fontSize: 10,
                    fontWeight: 600,
                    flexShrink: 0,
                    whiteSpace: "nowrap",
                  }}
                >
                  {step.from}
                </span>
                <span style={{ color: "var(--border-strong)", fontSize: 9, flexShrink: 0 }}>──</span>
                <span style={{ color: "var(--accent)", fontSize: 10, flex: 1, textAlign: "center", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{step.label}</span>
                <span style={{ color: "var(--border-strong)", fontSize: 9, flexShrink: 0 }}>──▶</span>
                <span
                  style={{
                    border: "1px solid var(--border)",
                    borderRadius: 3,
                    padding: "2px 6px",
                    fontSize: 10,
                    color: "var(--slate)",
                    flexShrink: 0,
                    whiteSpace: "nowrap",
                  }}
                >
                  {step.to}
                </span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Pricing ── */}
      <section
        id="pricing"
        style={{
          background: "var(--surface-2)",
          borderTop: "1px solid var(--border)",
          borderBottom: "1px solid var(--border)",
        }}
      >
        <div className="marketing-section" style={{ maxWidth: 1120, margin: "0 auto", padding: "80px 32px" }}>
          <div className="kicker" style={{ textAlign: "center", marginBottom: 12 }}>Get out now</div>
          <h2
            style={{
              fontSize: 36,
              fontWeight: 600,
              letterSpacing: "-0.03em",
              textAlign: "center",
              margin: "0 0 48px",
              color: "var(--ink)",
            }}
          >
            Start free.{" "}
            <span className="serif-i" style={{ color: "var(--accent)" }}>Scale without pain.</span>
          </h2>
          <div className="responsive-grid-3" style={{ gap: 16 }}>
            {PRICING.map((p) => (
              <div
                key={p.name}
                className="card"
                style={{
                  padding: 28,
                  position: "relative",
                  border: p.accent ? "1px solid var(--accent-border)" : undefined,
                  background: p.accent ? "var(--accent-soft)" : undefined,
                }}
              >
                {p.accent && (
                  <div
                    style={{
                      position: "absolute",
                      top: -1,
                      right: 20,
                      background: "var(--accent)",
                      color: "#fff",
                      fontSize: 10,
                      fontWeight: 700,
                      letterSpacing: "0.06em",
                      padding: "2px 10px",
                      borderRadius: "0 0 6px 6px",
                    }}
                  >
                    RECOMMENDED
                  </div>
                )}
                <div style={{ fontSize: 13.5, fontWeight: 600, marginBottom: 12, color: "var(--ink)" }}>{p.name}</div>
                <div style={{ marginBottom: 20 }}>
                  <span style={{ fontSize: 36, fontWeight: 700, letterSpacing: "-0.04em", color: "var(--ink)" }}>
                    {p.price}
                  </span>
                  <span style={{ fontSize: 14, color: "var(--muted)" }}>{p.period}</span>
                </div>
                <ul style={{ margin: "0 0 24px", padding: 0, listStyle: "none", display: "flex", flexDirection: "column", gap: 8 }}>
                  {p.features.map((f) => (
                    <li key={f} style={{ display: "flex", gap: 8, fontSize: 13, color: "var(--slate)" }}>
                      <span style={{ color: p.accent ? "var(--accent)" : "var(--green)", flexShrink: 0 }}>✓</span>
                      {f}
                    </li>
                  ))}
                </ul>
                <Link to="/onboarding" style={{ display: "block" }}>
                  <button
                    className={`btn btn-lg ${p.accent ? "btn-accent" : "btn-secondary"}`}
                    style={{ width: "100%" }}
                  >
                    {p.cta}
                  </button>
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Final CTA ── */}
      <section
        style={{
          background: "#0A0A0A",
          borderTop: "1px solid rgba(255,255,255,0.06)",
        }}
      >
        <div
          style={{
            maxWidth: 1120,
            margin: "0 auto",
            padding: "96px 32px",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            textAlign: "center",
          }}
        >
          <span className="badge badge-accent badge-mono" style={{ marginBottom: 20 }}>
            THE LAST MCP YOU'LL EVER NEED
          </span>
          <h2
            style={{
              fontSize: "clamp(32px, 5vw, 56px)",
              fontWeight: 600,
              letterSpacing: "-0.04em",
              lineHeight: 1.08,
              color: "#F4F3EE",
              margin: "0 0 20px",
            }}
          >
            Your agents are{" "}
            <span className="serif-i" style={{ color: "var(--accent)", fontSize: "1.05em" }}>
              bleeding context
            </span>
            <br />
            right now.
          </h2>
          <p
            style={{
              fontSize: 16,
              color: "#82817A",
              maxWidth: 520,
              margin: "0 0 40px",
              lineHeight: 1.65,
            }}
          >
            Every API you add without Harnex is another tool your agent has to juggle.
            The explosion compounds. Two tools. That's the exit.
          </p>
          <div style={{ display: "flex", gap: 10, justifyContent: "center" }}>
            {isAuthed ? (
              <Link to="/dashboard">
                <button className="btn btn-accent btn-lg">Open console →</button>
              </Link>
            ) : (
              <Link to="/onboarding">
                <button className="btn btn-accent btn-lg">
                  Start free — escape the explosion →
                </button>
              </Link>
            )}
            <a
              href="#the-problem"
              className="btn btn-ghost btn-lg"
              style={{
                textDecoration: "none",
                borderColor: "rgba(255,255,255,0.15)",
                color: "#B8B6AE",
              }}
            >
              Read the problem
            </a>
          </div>
          <div style={{ marginTop: 18, fontSize: 12, color: "#5C5B55" }}>
            No credit card required · Free tier available · Two tools, forever
          </div>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer style={{ borderTop: "1px solid var(--border)", marginTop: "auto" }}>
        <div
          style={{
            maxWidth: 1120,
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
            {["Docs", "Changelog", "Status", "Privacy", "Terms"].map((l) => (
              <a
                key={l}
                href="#"
                style={{ fontSize: 13, color: "var(--muted)", fontWeight: 500, textDecoration: "none" }}
              >
                {l}
              </a>
            ))}
          </nav>
        </div>
      </footer>
    </div>
    </>
  );
}
