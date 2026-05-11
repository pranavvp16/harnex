import { createFileRoute } from "@tanstack/react-router";

import { StatusBadge } from "@/components/ui/StatusBadge";

export const Route = createFileRoute("/_app/style-guide")({
  component: StyleGuide,
});

function StyleGuide() {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <div>
        <span className="kicker">Reference</span>
        <h2 className="h-display" style={{ fontSize: 28, margin: "8px 0 4px", fontWeight: 500 }}>
          Component <span className="serif-i">style guide</span>
        </h2>
        <p style={{ fontSize: 13, color: "var(--slate)", margin: 0 }}>
          Tokens and primitives used across the Harnex marketing site and console.
        </p>
      </div>

      <SgSection title="Colors">
        <div className="responsive-grid-4" style={{ gap: 10 }}>
          {[
            { n: "bg", v: "#F5F5F0" },
            { n: "surface", v: "#FFFFFF" },
            { n: "ink", v: "#0A0A0A" },
            { n: "slate", v: "#3F3F46" },
            { n: "muted", v: "#71717A" },
            { n: "border", v: "#E7E5E0" },
            { n: "accent", v: "#F97316" },
            { n: "accent-hover", v: "#EA580C" },
            { n: "green", v: "#16A34A" },
            { n: "amber", v: "#D97706" },
            { n: "red", v: "#DC2626" },
            { n: "accent-soft", v: "#FFF1E6" },
          ].map((s) => (
            <div key={s.n} className="card" style={{ overflow: "hidden" }}>
              <div style={{ height: 56, background: s.v, borderBottom: "1px solid var(--border)" }} />
              <div style={{ padding: 8 }}>
                <div className="mono" style={{ fontSize: 11, fontWeight: 500 }}>{s.n}</div>
                <div className="mono" style={{ fontSize: 10.5, color: "var(--muted)" }}>{s.v}</div>
              </div>
            </div>
          ))}
        </div>
      </SgSection>

      <SgSection title="Typography">
        <div className="card" style={{ padding: 20, display: "flex", flexDirection: "column", gap: 10 }}>
          <div>
            <span className="kicker">Display / Inter 500 + Newsreader italic</span>
            <div className="h-display" style={{ fontSize: 48, fontWeight: 500, marginTop: 4 }}>
              Connect <span className="serif-i">every</span> API.
            </div>
          </div>
          <div>
            <span className="kicker">H2 / 32</span>
            <div className="h-display" style={{ fontSize: 32, fontWeight: 500, marginTop: 4 }}>
              From spec to <span className="serif-i">agent-ready</span>.
            </div>
          </div>
          <div>
            <span className="kicker">H3 / 18</span>
            <div style={{ fontSize: 18, fontWeight: 500, marginTop: 4 }}>Connection health</div>
          </div>
          <div>
            <span className="kicker">Body / 14</span>
            <div style={{ fontSize: 14, color: "var(--slate)", marginTop: 4 }}>
              Harnex indexes your HTTP APIs and exposes secure search + execute through MCP.
            </div>
          </div>
          <div>
            <span className="kicker">Mono / JetBrains 12</span>
            <div className="mono" style={{ fontSize: 12, marginTop: 4 }}>
              GET /repos/{"{owner}"}/{"{repo}"}/pulls
            </div>
          </div>
        </div>
      </SgSection>

      <SgSection title="Buttons">
        <div className="card" style={{ padding: 16, display: "flex", gap: 8, flexWrap: "wrap" }}>
          <button className="btn btn-primary">Primary</button>
          <button className="btn btn-accent">Accent</button>
          <button className="btn btn-secondary">Secondary</button>
          <button className="btn btn-ghost">Ghost</button>
          <button className="btn btn-danger">Danger</button>
          <button className="btn btn-primary btn-sm">Small</button>
          <button className="btn btn-primary btn-lg">Large</button>
        </div>
      </SgSection>

      <SgSection title="Inputs & Selects">
        <div className="card responsive-grid-3" style={{ padding: 16, gap: 10 }}>
          <input className="input" placeholder="Default input" />
          <input className="input input-mono" placeholder="hx_live_••••" />
          <select className="select">
            <option>Bearer token</option>
            <option>OAuth</option>
          </select>
        </div>
      </SgSection>

      <SgSection title="Status badges">
        <div className="card" style={{ padding: 16, display: "flex", gap: 6, flexWrap: "wrap" }}>
          <StatusBadge status="ready" />
          <StatusBadge status="indexing" />
          <StatusBadge status="error" />
          <StatusBadge status="disabled" />
          <StatusBadge status="success" />
          <StatusBadge status="pending" />
          <StatusBadge status="timeout" />
          <span className="badge badge-accent">
            <span className="badge-dot" style={{ background: "var(--accent)" }} />
            Beta
          </span>
          <span className="method method-get">GET</span>
          <span className="method method-post">POST</span>
          <span className="method method-put">PUT</span>
          <span className="method method-delete">DELETE</span>
          <span className="method method-patch">PATCH</span>
        </div>
      </SgSection>

      <SgSection title="Alerts">
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          <div className="alert alert-info">{/* info icon */}<div>Indexing usually completes within 60 seconds.</div></div>
          <div className="alert alert-amber">{/* warning icon */}<div>Save this key now. Harnex will not show it again.</div></div>
          <div className="alert alert-red">{/* warning icon */}<div>Indexing failed. <span className="mono">401 Unauthorized</span></div></div>
          <div className="alert alert-accent">{/* spark icon */}<div>Connect your first API.</div></div>
        </div>
      </SgSection>

      <SgSection title="Empty state">
        <div className="card" style={{ padding: 40, textAlign: "center" }}>
          <div
            style={{
              width: 40,
              height: 40,
              margin: "0 auto 12px",
              background: "var(--bg-alt)",
              borderRadius: 999,
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
              color: "var(--muted)",
            }}
          >
            {/* plug icon */}
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M9 2v6M15 2v6M7 8h10v4a5 5 0 0 1-10 0zM12 17v5"/></svg>
          </div>
          <h3 style={{ fontSize: 15, fontWeight: 500, margin: "0 0 4px" }}>No connections yet</h3>
          <p style={{ fontSize: 12.5, color: "var(--muted)", margin: "0 0 12px" }}>
            Connect any HTTP API to make it agent-searchable.
          </p>
          <button className="btn btn-primary btn-sm">+ Connect an API</button>
        </div>
      </SgSection>
    </div>
  );
}

function SgSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", marginBottom: 8 }}>
        <h3 style={{ fontSize: 13, fontWeight: 500, margin: 0, color: "var(--slate)" }}>{title}</h3>
        <span style={{ flex: 1, height: 1, background: "var(--border)", marginLeft: 12 }} />
      </div>
      {children}
    </div>
  );
}
