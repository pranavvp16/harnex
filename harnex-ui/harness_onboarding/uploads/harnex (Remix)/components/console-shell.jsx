// Console Shell + all 8 console pages
const ConsoleShell = ({ onExitConsole, page, setPage, openConn, setOpenConn, density }) => {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "220px 1fr", height: "100%", background: "transparent", fontSize: density === "compact" ? 13 : 14, position: "relative", zIndex: 1 }}>
      <ConsoleSidebar page={page} setPage={setPage} onExitConsole={onExitConsole}/>
      <div style={{ display: "flex", flexDirection: "column", overflow: "hidden" }}>
        <ConsoleTopbar page={page}/>
        <div style={{ flex: 1, overflow: "auto" }}>
          {page === "dashboard" && <Dashboard setPage={setPage}/>}
          {page === "connections" && <ConnectionsList setPage={setPage} setOpenConn={setOpenConn}/>}
          {page === "new-connection" && <NewConnection setPage={setPage}/>}
          {page === "connection-detail" && <ConnectionDetail conn={openConn} setPage={setPage}/>}
          {page === "search" && <SearchPlayground/>}
          {page === "api-keys" && <ApiKeys/>}
          {page === "executions" && <Executions/>}
          {page === "usage" && <Usage/>}
          {page === "style-guide" && <StyleGuide/>}
          {page === "logos" && <LogoPage/>}
        </div>
      </div>
    </div>
  );
};

const ConsoleSidebar = ({ page, setPage, onExitConsole }) => {
  const nav = [
    { id: "dashboard", label: "Dashboard", icon: Ic.home },
    { id: "connections", label: "Connections", icon: Ic.plug, badge: "8" },
    { id: "search", label: "Search", icon: Ic.searchNav },
    { id: "api-keys", label: "API Keys", icon: Ic.key },
    { id: "executions", label: "Executions", icon: Ic.zap },
    { id: "usage", label: "Usage", icon: Ic.bar },
  ];
  const sub = [
    { id: "style-guide", label: "Style Guide", icon: Ic.command },
    { id: "logos", label: "Logo Marks", icon: Ic.spark },
  ];
  return (
    <aside style={{ background: "var(--surface-2)", borderRight: "1px solid var(--border)", display: "flex", flexDirection: "column", padding: "12px 10px" }}>
      <div style={{ padding: "6px 8px 12px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <button onClick={onExitConsole} title="Back to marketing site" style={{ background: "none", border: "none", padding: 0, cursor: "pointer" }}>
          <HarnexLogo size={20}/>
        </button>
        <span className="badge badge-slate" style={{ height: 18, fontSize: 10 }}>v0.4</span>
      </div>

      {/* Org switcher */}
      <button style={{ display: "flex", alignItems: "center", gap: 8, padding: "8px 8px", border: "1px solid var(--border)", borderRadius: 6, background: "var(--surface)", marginBottom: 12, cursor: "pointer", textAlign: "left" }}>
        <span style={{ width: 22, height: 22, borderRadius: 4, background: "var(--ink)", color: "#fff", display: "inline-flex", alignItems: "center", justifyContent: "center", fontSize: 11, fontWeight: 600 }}>A</span>
        <span style={{ flex: 1, fontSize: 12.5, fontWeight: 500 }}>acme-corp</span>
        <span style={{ color: "var(--muted)" }}>{Ic.chev}</span>
      </button>

      <div style={{ display: "flex", flexDirection: "column", gap: 1 }}>
        {nav.map(n => {
          const active = page === n.id || (n.id === "connections" && (page === "connection-detail" || page === "new-connection"));
          return (
            <button key={n.id} onClick={() => setPage(n.id)} style={{ display: "flex", alignItems: "center", gap: 9, padding: "6px 8px", border: "none", borderRadius: 5, background: active ? "var(--surface)" : "transparent", color: active ? "var(--ink)" : "var(--slate)", fontSize: 12.5, fontWeight: active ? 500 : 400, cursor: "pointer", textAlign: "left", boxShadow: active ? "var(--shadow-sm)" : "none", border: active ? "1px solid var(--border)" : "1px solid transparent" }}>
              <span style={{ display: "inline-flex", color: active ? "var(--ink)" : "var(--muted)" }}>{n.icon}</span>
              <span style={{ flex: 1 }}>{n.label}</span>
              {n.badge && <span className="mono" style={{ fontSize: 10.5, color: "var(--muted)" }}>{n.badge}</span>}
            </button>
          );
        })}
      </div>

      <div style={{ marginTop: 18, padding: "0 8px 6px" }} className="kicker">Reference</div>
      <div style={{ display: "flex", flexDirection: "column", gap: 1 }}>
        {sub.map(n => {
          const active = page === n.id;
          return (
            <button key={n.id} onClick={() => setPage(n.id)} style={{ display: "flex", alignItems: "center", gap: 9, padding: "6px 8px", border: "none", borderRadius: 5, background: active ? "var(--surface)" : "transparent", color: active ? "var(--ink)" : "var(--slate)", fontSize: 12.5, cursor: "pointer", textAlign: "left", border: active ? "1px solid var(--border)" : "1px solid transparent" }}>
              <span style={{ display: "inline-flex", color: active ? "var(--ink)" : "var(--muted)" }}>{n.icon}</span>
              <span>{n.label}</span>
            </button>
          );
        })}
      </div>

      <div style={{ marginTop: "auto", borderTop: "1px solid var(--border)", paddingTop: 12, display: "flex", flexDirection: "column", gap: 6 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "6px 8px" }}>
          <span style={{ width: 24, height: 24, borderRadius: 999, background: "linear-gradient(135deg, #0A0A0A, #3F3F46)", color: "#fff", display: "inline-flex", alignItems: "center", justifyContent: "center", fontSize: 10.5, fontWeight: 600 }}>JS</span>
          <div style={{ display: "flex", flexDirection: "column", lineHeight: 1.2 }}>
            <span style={{ fontSize: 12, fontWeight: 500 }}>Jamie Solis</span>
            <span style={{ fontSize: 10.5, color: "var(--muted)" }}>jamie@acme.dev</span>
          </div>
          <span style={{ marginLeft: "auto", color: "var(--muted)" }}>{Ic.settings}</span>
        </div>
      </div>
    </aside>
  );
};

const ConsoleTopbar = ({ page }) => {
  const titles = {
    dashboard: "Dashboard",
    connections: "Connections",
    "new-connection": "New connection",
    "connection-detail": "Connection",
    search: "Search playground",
    "api-keys": "API keys",
    executions: "Executions",
    usage: "Usage",
    "style-guide": "Style guide",
    logos: "Logo marks",
  };
  return (
    <div style={{ height: 44, borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", padding: "0 20px", gap: 12, background: "var(--bg)" }}>
      <h1 style={{ fontSize: 14, fontWeight: 500, margin: 0 }}>{titles[page] || "Harnex"}</h1>
      <span style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 8 }}>
        <button className="btn btn-ghost btn-sm">{Ic.book} Docs</button>
        <button className="btn btn-ghost btn-sm" style={{ width: 28, padding: 0 }}>{Ic.bell}</button>
        <span className="mono" style={{ fontSize: 11, color: "var(--muted)", border: "1px solid var(--border)", padding: "2px 6px", borderRadius: 4, background: "var(--surface)" }}>⌘K</span>
      </span>
    </div>
  );
};

// ────────────────────────── DASHBOARD ──────────────────────────
const Dashboard = ({ setPage }) => {
  const ready = SampleConnections.filter(c => c.status === "ready").length;
  const indexing = SampleConnections.filter(c => c.status === "indexing").length;
  const errored = SampleConnections.filter(c => c.status === "error").length;

  return (
    <div style={{ padding: 20, display: "flex", flexDirection: "column", gap: 16 }}>
      {/* Banner */}
      <div className="alert alert-accent" style={{ alignItems: "center" }}>
        <span style={{ display: "inline-flex" }}>{Ic.spark}</span>
        <div style={{ flex: 1 }}>
          <strong style={{ fontWeight: 500 }}>Connect your first API.</strong>
          <span style={{ marginLeft: 8, color: "var(--accent-ink)", opacity: 0.85 }}>Index any HTTP API in under a minute.</span>
        </div>
        <button className="btn btn-accent btn-sm" onClick={() => setPage("new-connection")}>{Ic.plus} Connect an API</button>
      </div>

      {/* KPIs */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12 }}>
        <KpiCard label="Connections" value="8" sub="6 ready · 1 indexing · 1 error" trend="+2 this week"/>
        <KpiCard label="Executions" value="14,238" sub="this month" trend="+18% vs last" trendUp/>
        <KpiCard label="Searches" value="3,184" sub="this month" trend="+22% vs last" trendUp/>
        <KpiCard label="P95 latency" value="221ms" sub="last 24h" trend="−12ms vs last week" trendUp/>
      </div>

      {/* Two-col */}
      <div style={{ display: "grid", gridTemplateColumns: "1.4fr 1fr", gap: 12 }}>
        {/* Recent executions */}
        <div className="card">
          <div style={{ padding: "12px 16px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", gap: 8 }}>
            <h3 style={{ fontSize: 13, fontWeight: 500, margin: 0 }}>Recent executions</h3>
            <span className="badge badge-slate" style={{ height: 18, fontSize: 10 }}>last 1h</span>
            <button className="btn btn-ghost btn-sm" style={{ marginLeft: "auto" }} onClick={() => setPage("executions")}>View all {Ic.arrow}</button>
          </div>
          <table className="tbl">
            <thead>
              <tr>
                <th>When</th>
                <th>Operation</th>
                <th>Status</th>
                <th style={{ textAlign: "right" }}>Duration</th>
              </tr>
            </thead>
            <tbody>
              {SampleExecutions.slice(0, 7).map(e => (
                <tr key={e.id} className="row-hover">
                  <td className="mono" style={{ fontSize: 11.5, color: "var(--muted)" }}>{e.when.split(" ")[1]}</td>
                  <td>
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <span className={`method method-${e.op.split(" ")[0].toLowerCase()}`}>{e.op.split(" ")[0]}</span>
                      <span className="mono" style={{ fontSize: 12 }}>{e.op.split(" ").slice(1).join(" ")}</span>
                    </div>
                  </td>
                  <td><StatusBadge s={e.status}/></td>
                  <td className="mono" style={{ fontSize: 11.5, color: "var(--muted)", textAlign: "right" }}>{e.dur}ms</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Health + quota */}
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <div className="card" style={{ padding: 16 }}>
            <div style={{ display: "flex", alignItems: "center", marginBottom: 14 }}>
              <h3 style={{ fontSize: 13, fontWeight: 500, margin: 0 }}>Connection health</h3>
              <button className="btn btn-ghost btn-sm" style={{ marginLeft: "auto" }} onClick={() => setPage("connections")}>Manage {Ic.arrow}</button>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 8 }}>
              <HealthBox label="Ready" count={ready} color="green"/>
              <HealthBox label="Indexing" count={indexing} color="amber"/>
              <HealthBox label="Errored" count={errored} color="red"/>
            </div>
            <div style={{ height: 16 }}/>
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              {SampleConnections.slice(0, 4).map(c => (
                <div key={c.id} style={{ display: "flex", alignItems: "center", gap: 8, padding: "5px 0" }}>
                  <span style={{ display: "inline-flex" }}>{React.cloneElement(Marks[c.connector] || Marks.openapi, { size: 14 })}</span>
                  <span className="mono" style={{ fontSize: 12 }}>{c.name}</span>
                  <span style={{ marginLeft: "auto" }}><StatusBadge s={c.status}/></span>
                </div>
              ))}
            </div>
          </div>

          <div className="card" style={{ padding: 16 }}>
            <div style={{ display: "flex", alignItems: "center", marginBottom: 12 }}>
              <h3 style={{ fontSize: 13, fontWeight: 500, margin: 0 }}>Usage quota</h3>
              <span style={{ marginLeft: "auto", fontSize: 11.5, color: "var(--muted)" }} className="mono">team plan · resets May 1</span>
            </div>
            <QuotaRow label="Executions" used={14238} cap={250000}/>
            <QuotaRow label="Searches" used={3184} cap={50000}/>
            <QuotaRow label="Embedding tokens" used={1820000} cap={5000000} unit="tok"/>
          </div>
        </div>
      </div>
    </div>
  );
};

const KpiCard = ({ label, value, sub, trend, trendUp }) => (
  <div className="card" style={{ padding: 14 }}>
    <div className="kicker">{label}</div>
    <div className="h-display" style={{ fontSize: 28, marginTop: 6, fontWeight: 500 }}>{value}</div>
    <div style={{ fontSize: 11.5, color: "var(--muted)", marginTop: 2 }}>{sub}</div>
    {trend && <div style={{ fontSize: 11, color: trendUp ? "var(--green-ink)" : "var(--muted)", marginTop: 6 }}>{trend}</div>}
  </div>
);

const HealthBox = ({ label, count, color }) => {
  const map = { green: { bg: "var(--green-soft)", b: "var(--green-border)", c: "var(--green-ink)" }, amber: { bg: "var(--amber-soft)", b: "var(--amber-border)", c: "var(--amber-ink)" }, red: { bg: "var(--red-soft)", b: "var(--red-border)", c: "var(--red-ink)" } };
  const v = map[color];
  return (
    <div style={{ background: v.bg, border: `1px solid ${v.b}`, borderRadius: 6, padding: "10px 12px" }}>
      <div className="h-display" style={{ fontSize: 22, color: v.c, fontWeight: 500 }}>{count}</div>
      <div style={{ fontSize: 11, color: v.c, opacity: 0.8 }}>{label}</div>
    </div>
  );
};

const QuotaRow = ({ label, used, cap, unit }) => {
  const pct = Math.min(100, (used / cap) * 100);
  const color = pct > 80 ? "var(--accent)" : pct > 60 ? "var(--amber)" : "var(--ink)";
  return (
    <div style={{ marginBottom: 10 }}>
      <div style={{ display: "flex", alignItems: "center", marginBottom: 4 }}>
        <span style={{ fontSize: 12 }}>{label}</span>
        <span className="mono" style={{ marginLeft: "auto", fontSize: 11, color: "var(--muted)" }}>
          {used.toLocaleString()}{unit ? unit : ""} / {cap.toLocaleString()}{unit ? unit : ""}
        </span>
      </div>
      <div style={{ height: 5, background: "var(--border)", borderRadius: 3, overflow: "hidden" }}>
        <div style={{ width: `${pct}%`, height: "100%", background: color }}/>
      </div>
    </div>
  );
};

const StatusBadge = ({ s }) => {
  const m = {
    ready: { c: "green", l: "Ready" },
    success: { c: "green", l: "success" },
    indexing: { c: "amber", l: "Indexing" },
    pending: { c: "amber", l: "pending" },
    timeout: { c: "amber", l: "timeout" },
    error: { c: "red", l: "Error" },
    disabled: { c: "slate", l: "Disabled" },
  };
  const v = m[s] || { c: "slate", l: s };
  return <span className={`badge badge-${v.c}`}><span className={`badge-dot`} style={{ background: `var(--${v.c === "slate" ? "muted" : v.c})` }}/>{v.l}</span>;
};

window.ConsoleShell = ConsoleShell;
window.StatusBadge = StatusBadge;
window.QuotaRow = QuotaRow;
