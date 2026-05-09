// Style Guide + Logo page
const StyleGuide = () => {
  return (
    <div style={{ padding: 20, display: "flex", flexDirection: "column", gap: 16 }}>
      <div>
        <span className="kicker">Reference</span>
        <h2 className="h-display" style={{ fontSize: 28, margin: "8px 0 4px", fontWeight: 500 }}>Component <span className="serif-i">style guide</span></h2>
        <p style={{ fontSize: 13, color: "var(--slate)", margin: 0 }}>Tokens and primitives used across the Harnex marketing site and console.</p>
      </div>

      <SgSection title="Colors">
        <div style={{ display: "grid", gridTemplateColumns: "repeat(6, 1fr)", gap: 10 }}>
          {[
            { n: "bg", v: "#F5F5F0" }, { n: "surface", v: "#FFFFFF" }, { n: "ink", v: "#0A0A0A" }, { n: "slate", v: "#3F3F46" }, { n: "muted", v: "#71717A" }, { n: "border", v: "#E7E5E0" },
            { n: "accent", v: "#F97316" }, { n: "accent-hover", v: "#EA580C" }, { n: "green", v: "#16A34A" }, { n: "amber", v: "#D97706" }, { n: "red", v: "#DC2626" }, { n: "accent-soft", v: "#FFF1E6" },
          ].map(s => (
            <div key={s.n} className="card" style={{ overflow: "hidden" }}>
              <div style={{ height: 56, background: s.v, borderBottom: "1px solid var(--border)" }}/>
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
          <div><span className="kicker">Display / Inter 500 + Newsreader italic</span><div className="h-display" style={{ fontSize: 48, fontWeight: 500, marginTop: 4 }}>Connect <span className="serif-i">every</span> API.</div></div>
          <div><span className="kicker">H2 / 32</span><div className="h-display" style={{ fontSize: 32, fontWeight: 500, marginTop: 4 }}>From spec to <span className="serif-i">agent-ready</span>.</div></div>
          <div><span className="kicker">H3 / 18</span><div style={{ fontSize: 18, fontWeight: 500, marginTop: 4 }}>Connection health</div></div>
          <div><span className="kicker">Body / 14</span><div style={{ fontSize: 14, color: "var(--slate)", marginTop: 4 }}>Harnex indexes your HTTP APIs and exposes secure search + execute through MCP.</div></div>
          <div><span className="kicker">Mono / JetBrains 12</span><div className="mono" style={{ fontSize: 12, marginTop: 4 }}>GET /repos/{"{owner}"}/{"{repo}"}/pulls</div></div>
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
          <button className="btn btn-secondary">{Ic.plus} With icon</button>
        </div>
      </SgSection>

      <SgSection title="Inputs & Selects">
        <div className="card" style={{ padding: 16, display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 10 }}>
          <input className="input" placeholder="Default input"/>
          <input className="input input-mono" placeholder="hx_live_••••"/>
          <select className="select"><option>Bearer token</option><option>OAuth</option></select>
        </div>
      </SgSection>

      <SgSection title="Status badges">
        <div className="card" style={{ padding: 16, display: "flex", gap: 6, flexWrap: "wrap" }}>
          <StatusBadge s="ready"/><StatusBadge s="indexing"/><StatusBadge s="error"/><StatusBadge s="disabled"/>
          <StatusBadge s="success"/><StatusBadge s="pending"/><StatusBadge s="timeout"/>
          <span className="badge badge-accent"><span className="badge-dot" style={{ background: "var(--accent)" }}/>Beta</span>
          <span className="method method-get">GET</span>
          <span className="method method-post">POST</span>
          <span className="method method-put">PUT</span>
          <span className="method method-delete">DELETE</span>
          <span className="method method-patch">PATCH</span>
        </div>
      </SgSection>

      <SgSection title="Alerts">
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          <div className="alert alert-info">{Ic.info}<div>Indexing usually completes within 60 seconds.</div></div>
          <div className="alert alert-amber">{Ic.warning}<div>Save this key now. Harnex will not show it again.</div></div>
          <div className="alert alert-red">{Ic.warning}<div>Indexing failed. <span className="mono">401 Unauthorized</span></div></div>
          <div className="alert alert-accent">{Ic.spark}<div>Connect your first API.</div></div>
        </div>
      </SgSection>

      <SgSection title="Empty state">
        <div className="card" style={{ padding: 40, textAlign: "center" }}>
          <div style={{ width: 40, height: 40, margin: "0 auto 12px", background: "var(--bg-alt)", borderRadius: 999, display: "inline-flex", alignItems: "center", justifyContent: "center", color: "var(--muted)" }}>{Ic.plug}</div>
          <h3 style={{ fontSize: 15, fontWeight: 500, margin: "0 0 4px" }}>No connections yet</h3>
          <p style={{ fontSize: 12.5, color: "var(--muted)", margin: "0 0 12px" }}>Connect any HTTP API to make it agent-searchable.</p>
          <button className="btn btn-primary btn-sm">{Ic.plus} Connect an API</button>
        </div>
      </SgSection>

      <SgSection title="Connector tile">
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 10, maxWidth: 720 }}>
          {["github","stripe","openapi"].map(k => (
            <div key={k} style={{ padding: 14, border: "1px solid var(--border)", borderRadius: 8, background: "var(--surface)", display: "flex", gap: 12, alignItems: "center" }}>
              <div style={{ width: 36, height: 36, borderRadius: 6, background: "var(--bg-alt)", border: "1px solid var(--border)", display: "inline-flex", alignItems: "center", justifyContent: "center" }}>{React.cloneElement(Marks[k], { size: 20 })}</div>
              <div><div style={{ fontSize: 13, fontWeight: 500 }}>{k}</div><div style={{ fontSize: 11, color: "var(--muted)" }}>connector tile</div></div>
            </div>
          ))}
        </div>
      </SgSection>
    </div>
  );
};

const SgSection = ({ title, children }) => (
  <div>
    <div style={{ display: "flex", alignItems: "center", marginBottom: 8 }}>
      <h3 style={{ fontSize: 13, fontWeight: 500, margin: 0, color: "var(--slate)" }}>{title}</h3>
      <span style={{ flex: 1, height: 1, background: "var(--border)", marginLeft: 12 }}/>
    </div>
    {children}
  </div>
);

const LogoPage = () => (
  <div style={{ padding: 20, display: "flex", flexDirection: "column", gap: 16 }}>
    <div>
      <span className="kicker">Brand</span>
      <h2 className="h-display" style={{ fontSize: 28, margin: "8px 0 4px", fontWeight: 500 }}>Logo <span className="serif-i">marks</span></h2>
      <p style={{ fontSize: 13, color: "var(--slate)", margin: 0 }}>Two directions. Both use the warm orange accent and a bracketed connection metaphor.</p>
    </div>

    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
      {[
        { Cmp: HarnexLogo, title: "01 — Bracketed bar", note: "Two brackets cradle a horizontal connector. Reads as “API endpoints linked by Harnex.”" },
        { Cmp: HarnexLogoAlt, title: "02 — Chevron H", note: "A command-prompt chevron paired with an H stem. Feels like a dev-tool CLI." },
      ].map((d, i) => (
        <div key={i} className="card" style={{ padding: 0, overflow: "hidden" }}>
          <div style={{ padding: "10px 14px", borderBottom: "1px solid var(--border)", background: "var(--surface-2)", display: "flex", alignItems: "center" }}>
            <span className="kicker">{d.title}</span>
          </div>
          <div style={{ padding: 24, background: "var(--bg-alt)", borderBottom: "1px solid var(--border)", display: "flex", justifyContent: "center", alignItems: "center", minHeight: 120 }}>
            <d.Cmp size={36}/>
          </div>
          <div style={{ padding: 24, background: "var(--ink)", borderBottom: "1px solid var(--border)", display: "flex", justifyContent: "center", alignItems: "center", minHeight: 120 }}>
            <d.Cmp size={36} dark/>
          </div>
          <div style={{ padding: 16, display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, alignItems: "center" }}>
            <div style={{ textAlign: "center" }}><d.Cmp size={48} showWordmark={false}/><div style={{ fontSize: 10, color: "var(--muted)", marginTop: 6 }} className="mono">48px</div></div>
            <div style={{ textAlign: "center" }}><d.Cmp size={32} showWordmark={false}/><div style={{ fontSize: 10, color: "var(--muted)", marginTop: 6 }} className="mono">32px</div></div>
            <div style={{ textAlign: "center" }}><d.Cmp size={20} showWordmark={false}/><div style={{ fontSize: 10, color: "var(--muted)", marginTop: 6 }} className="mono">20px</div></div>
            <div style={{ textAlign: "center" }}><d.Cmp size={14} showWordmark={false}/><div style={{ fontSize: 10, color: "var(--muted)", marginTop: 6 }} className="mono">favicon</div></div>
          </div>
          <div style={{ padding: "12px 16px", borderTop: "1px solid var(--border)", fontSize: 12.5, color: "var(--slate)" }}>{d.note}</div>
        </div>
      ))}
    </div>

    <div className="card" style={{ padding: 20 }}>
      <h3 style={{ fontSize: 13, fontWeight: 500, margin: "0 0 12px" }}>In context</h3>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
        <div style={{ border: "1px solid var(--border)", borderRadius: 8, padding: 14, background: "var(--surface)", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <HarnexLogo size={20}/>
          <div style={{ display: "flex", gap: 8 }}><button className="btn btn-ghost btn-sm">Sign in</button><button className="btn btn-primary btn-sm">Get started</button></div>
        </div>
        <div style={{ border: "1px solid var(--border)", borderRadius: 8, padding: 14, background: "var(--ink)", color: "#fff", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <HarnexLogo size={20} dark/>
          <span style={{ fontSize: 11, color: "rgba(255,255,255,0.6)" }} className="mono">app.harnex.dev</span>
        </div>
      </div>
    </div>
  </div>
);

window.StyleGuide = StyleGuide;
window.LogoPage = LogoPage;
