// Search Playground, API Keys, Executions, Usage
const SearchPlayground = () => {
  const [query, setQuery] = React.useState("list pull requests for repo");
  const [topK, setTopK] = React.useState(5);
  const [connector, setConnector] = React.useState("all");
  const [results, setResults] = React.useState(SampleOperations);
  const [loading, setLoading] = React.useState(false);
  const [showAmbig, setShowAmbig] = React.useState(false);

  const search = () => {
    setLoading(true);
    setShowAmbig(query.toLowerCase().includes("update") && !query.includes("pull"));
    setTimeout(() => {
      const q = query.toLowerCase();
      const filtered = SampleOperations
        .filter(o => connector === "all" || o.connector === connector)
        .map(o => {
          // simple keyword scoring
          const text = (o.summary + " " + o.path + " " + o.opId).toLowerCase();
          const tokens = q.split(/\s+/).filter(Boolean);
          const hits = tokens.filter(t => text.includes(t)).length;
          const baseScore = o.score;
          const adj = tokens.length === 0 ? baseScore : Math.min(0.99, 0.4 + 0.12 * hits + baseScore * 0.5);
          return { ...o, score: parseFloat(adj.toFixed(2)) };
        })
        .sort((a, b) => b.score - a.score)
        .slice(0, topK);
      setResults(filtered);
      setLoading(false);
    }, 350);
  };

  React.useEffect(() => { search(); }, []);

  const exampleQueries = [
    "list pull requests for repo",
    "create a stripe customer",
    "post a slack message",
    "list datadog incidents in last 24h",
    "update a linear issue's status",
  ];

  return (
    <div style={{ padding: 20, display: "grid", gridTemplateColumns: "1.4fr 1fr", gap: 14, height: "100%" }}>
      <div style={{ display: "flex", flexDirection: "column", gap: 12, minHeight: 0 }}>
        <div className="card" style={{ padding: 14, display: "flex", flexDirection: "column", gap: 10 }}>
          <div style={{ position: "relative" }}>
            <span style={{ position: "absolute", left: 12, top: 11, color: "var(--muted)" }}>{Ic.search}</span>
            <input className="input" value={query} onChange={e => setQuery(e.target.value)} onKeyDown={e => e.key === "Enter" && search()} placeholder='Try: "list pull requests for repo"' style={{ height: 40, paddingLeft: 34, fontSize: 14 }}/>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <select className="select" style={{ width: 180 }} value={connector} onChange={e => setConnector(e.target.value)}>
              <option value="all">All connectors</option>
              <option value="github">GitHub</option>
              <option value="stripe">Stripe</option>
              <option value="linear">Linear</option>
              <option value="datadog">Datadog</option>
              <option value="slack">Slack</option>
            </select>
            <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <span style={{ fontSize: 12, color: "var(--muted)" }}>top_k</span>
              <input type="number" className="input" min={1} max={20} value={topK} onChange={e => setTopK(parseInt(e.target.value) || 5)} style={{ width: 64 }}/>
            </div>
            <span style={{ flex: 1 }}/>
            <button className="btn btn-primary btn-sm" onClick={search}>{Ic.search} Search</button>
          </div>
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap", paddingTop: 4 }}>
            {exampleQueries.map(q => (
              <button key={q} onClick={() => { setQuery(q); setTimeout(search, 0); }} style={{ fontSize: 11.5, padding: "3px 8px", background: "var(--surface-2)", border: "1px solid var(--border)", borderRadius: 999, color: "var(--slate)", cursor: "pointer" }}>{q}</button>
            ))}
          </div>
        </div>

        {showAmbig && (
          <div className="alert alert-amber">
            <span style={{ display: "inline-flex" }}>{Ic.warning}</span>
            <div>
              <strong>Ambiguous query.</strong> Multiple operations matched. Consider clarifying which resource (e.g. "update a Linear <em>issue</em> status" vs. "update a GitHub <em>PR</em>").
            </div>
          </div>
        )}

        <div className="card" style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden", minHeight: 0 }}>
          <div style={{ padding: "10px 14px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center" }}>
            <span className="kicker">Results</span>
            <span style={{ marginLeft: "auto", fontSize: 11, color: "var(--muted)" }} className="mono">
              {loading ? "searching…" : `${results.length} results · ${(Math.random()*60+40).toFixed(0)}ms`}
            </span>
          </div>
          <div style={{ flex: 1, overflow: "auto", padding: 10, display: "flex", flexDirection: "column", gap: 8 }}>
            {loading && <div style={{ padding: 30, textAlign: "center", color: "var(--muted)", fontSize: 12.5 }}>Searching across operations…</div>}
            {!loading && results.length === 0 && (
              <div style={{ padding: 30, textAlign: "center", color: "var(--muted)" }}>
                <div style={{ marginBottom: 6 }}>{Ic.search}</div>
                <div style={{ fontSize: 13 }}>No operations matched.</div>
              </div>
            )}
            {!loading && results.map((r, i) => (
              <div key={i} style={{ border: "1px solid var(--border)", borderRadius: 6, padding: "10px 12px", background: i === 0 ? "var(--accent-soft)" : "var(--surface)", borderColor: i === 0 ? "var(--accent-border)" : "var(--border)" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <span className={`method method-${r.method.toLowerCase()}`}>{r.method}</span>
                  <span className="mono" style={{ fontSize: 12.5, fontWeight: 500 }}>{r.path}</span>
                  <span style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 8 }}>
                    <span style={{ display: "inline-flex", alignItems: "center", gap: 4, fontSize: 11.5, color: "var(--muted)" }}>
                      {React.cloneElement(Marks[r.connector] || Marks.openapi, { size: 12 })}
                      {r.connectorName}
                    </span>
                    <span className="mono" style={{ fontSize: 11, padding: "2px 6px", borderRadius: 3, background: i === 0 ? "rgba(154,52,18,0.12)" : "var(--bg-alt)", color: i === 0 ? "var(--accent-ink)" : "var(--slate)", fontWeight: 500 }}>{r.score.toFixed(2)}</span>
                  </span>
                </div>
                <div style={{ fontSize: 12.5, color: "var(--slate)", marginTop: 4 }}>{r.summary}</div>
                <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 4 }}>
                  <span className="mono" style={{ fontSize: 11, color: "var(--muted)" }}>op: {r.opId}</span>
                  <span style={{ marginLeft: "auto" }}>
                    <button className="btn btn-ghost btn-sm" style={{ height: 22, fontSize: 11 }}>{Ic.terminal} Try execute</button>
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right: MCP request preview */}
      <div className="card" style={{ display: "flex", flexDirection: "column", overflow: "hidden", minHeight: 0 }}>
        <div style={{ padding: "10px 14px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", gap: 6 }}>
          <span className="kicker">MCP request</span>
          <span style={{ marginLeft: "auto" }}>
            <button className="btn btn-ghost btn-sm">{Ic.copy} Copy</button>
          </span>
        </div>
        <pre style={{ margin: 0, padding: 14, fontFamily: "var(--font-mono)", fontSize: 11.5, color: "var(--slate)", overflow: "auto", lineHeight: 1.5, flex: 1 }}>
{`POST /mcp/v1/tools/search
Authorization: Bearer hx_live_•••••
Content-Type: application/json

{
  "query": ${JSON.stringify(query)},
  "top_k": ${topK},
  "filter": {
    "connector": ${JSON.stringify(connector)}
  }
}

→ 200 OK · 84ms

{
  "results": [
${results.slice(0, 3).map(r => `    {
      "method": "${r.method}",
      "path": "${r.path}",
      "summary": "${r.summary}",
      "connector": "${r.connector}",
      "operation_id": "${r.opId}",
      "score": ${r.score.toFixed(2)}
    }`).join(",\n")}${results.length > 3 ? ",\n    ..." : ""}
  ]
}`}
        </pre>
      </div>
    </div>
  );
};

const ApiKeys = () => {
  const [showNew, setShowNew] = React.useState(false);
  const [created, setCreated] = React.useState(false);
  const [name, setName] = React.useState("");

  return (
    <div style={{ padding: 20, display: "flex", flexDirection: "column", gap: 14 }}>
      {!showNew ? (
        <>
          <div style={{ display: "flex", alignItems: "center" }}>
            <div>
              <h2 className="h-display" style={{ fontSize: 20, margin: 0, fontWeight: 500 }}>API <span className="serif-i">keys</span></h2>
              <p style={{ fontSize: 12.5, color: "var(--muted)", margin: "4px 0 0" }}>Keys authenticate your agents and runtime against the Harnex MCP server.</p>
            </div>
            <span style={{ flex: 1 }}/>
            <button className="btn btn-primary btn-sm" onClick={() => { setShowNew(true); setCreated(false); }}>{Ic.plus} Issue new key</button>
          </div>

          <div className="card" style={{ overflow: "hidden" }}>
            <table className="tbl">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Prefix</th>
                  <th>Last used</th>
                  <th>Created</th>
                  <th style={{ width: 100, textAlign: "right" }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {SampleApiKeys.map(k => (
                  <tr key={k.id} className="row-hover">
                    <td><span style={{ fontWeight: 500, fontSize: 13 }}>{k.name}</span></td>
                    <td><span className="mono" style={{ fontSize: 12 }}>{k.prefix}_••••••••</span></td>
                    <td><span className="mono" style={{ fontSize: 11.5, color: "var(--muted)" }}>{k.lastUsed}</span></td>
                    <td><span className="mono" style={{ fontSize: 11.5, color: "var(--muted)" }}>{k.created}</span></td>
                    <td style={{ textAlign: "right" }}>
                      <button className="btn btn-danger btn-sm">Revoke</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      ) : (
        <div className="card" style={{ padding: 20, maxWidth: 600 }}>
          <div style={{ display: "flex", alignItems: "center", marginBottom: 14 }}>
            <h2 className="h-display" style={{ fontSize: 20, margin: 0, fontWeight: 500 }}>Issue new key</h2>
            <span style={{ flex: 1 }}/>
            <button className="btn btn-ghost btn-sm" onClick={() => setShowNew(false)}>{Ic.x}</button>
          </div>

          {!created ? (
            <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
              <Field label="Key name" hint="Used in audit logs and the keys list.">
                <input className="input" value={name} onChange={e => setName(e.target.value)} placeholder="production-agent"/>
              </Field>
              <Field label="Scope">
                <select className="select">
                  <option>All connections</option>
                  <option>Specific connections…</option>
                </select>
              </Field>
              <Field label="Expires">
                <select className="select">
                  <option>Never</option>
                  <option>30 days</option>
                  <option>90 days</option>
                  <option>1 year</option>
                </select>
              </Field>
              <div style={{ display: "flex", gap: 8, marginTop: 4 }}>
                <span style={{ flex: 1 }}/>
                <button className="btn btn-ghost" onClick={() => setShowNew(false)}>Cancel</button>
                <button className="btn btn-accent" onClick={() => setCreated(true)}>Issue key</button>
              </div>
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
              <div className="alert alert-amber">
                <span style={{ display: "inline-flex" }}>{Ic.warning}</span>
                <div>
                  <strong>Save this key now.</strong> Harnex will not show it again. Treat it like a password.
                </div>
              </div>
              <div style={{ background: "var(--ink)", color: "#FAFAF7", padding: 14, borderRadius: 6, display: "flex", alignItems: "center", gap: 10 }}>
                <span className="mono" style={{ flex: 1, fontSize: 12.5, wordBreak: "break-all" }}>hx_live_R3kQ8FtNm2pXJv9LcKjP7WqB4Yh5DsFa</span>
                <button className="btn btn-ghost btn-sm" style={{ background: "rgba(255,255,255,0.08)", color: "#fff", borderColor: "rgba(255,255,255,0.2)" }}>{Ic.copy} Copy</button>
              </div>
              <div style={{ display: "flex", gap: 8 }}>
                <span style={{ flex: 1 }}/>
                <button className="btn btn-primary" onClick={() => setShowNew(false)}>Done</button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

const Executions = () => {
  const [statusF, setStatusF] = React.useState("all");
  const [search, setSearch] = React.useState("");
  const filtered = SampleExecutions.filter(e =>
    (statusF === "all" || e.status === statusF) &&
    (search === "" || e.op.toLowerCase().includes(search.toLowerCase()))
  );

  return (
    <div style={{ padding: 20, display: "flex", flexDirection: "column", gap: 14 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <div style={{ position: "relative", width: 320 }}>
          <span style={{ position: "absolute", left: 10, top: 9, color: "var(--muted)" }}>{Ic.search}</span>
          <input className="input" value={search} onChange={e => setSearch(e.target.value)} placeholder="Filter by operation path" style={{ paddingLeft: 30 }}/>
        </div>
        <select className="select" style={{ width: 140 }} value={statusF} onChange={e => setStatusF(e.target.value)}>
          <option value="all">All statuses</option>
          <option value="success">Success</option>
          <option value="error">Error</option>
          <option value="timeout">Timeout</option>
          <option value="pending">Pending</option>
        </select>
        <select className="select" style={{ width: 140 }}>
          <option>Last 1h</option>
          <option>Last 24h</option>
          <option>Last 7d</option>
          <option>Last 30d</option>
        </select>
        <span style={{ flex: 1 }}/>
        <button className="btn btn-ghost btn-sm">Export CSV</button>
      </div>

      <div className="card" style={{ overflow: "hidden" }}>
        <table className="tbl">
          <thead>
            <tr>
              <th style={{ width: 160 }}>When</th>
              <th>Operation</th>
              <th>Mode</th>
              <th>Status</th>
              <th style={{ textAlign: "right" }}>Duration</th>
              <th style={{ width: 30 }}></th>
            </tr>
          </thead>
          <tbody>
            {filtered.map(e => (
              <tr key={e.id} className="row-hover">
                <td className="mono" style={{ fontSize: 11.5, color: "var(--muted)" }}>{e.when}</td>
                <td>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <span className={`method method-${e.op.split(" ")[0].toLowerCase()}`}>{e.op.split(" ")[0]}</span>
                    <span className="mono" style={{ fontSize: 12 }}>{e.op.split(" ").slice(1).join(" ")}</span>
                    <span style={{ display: "inline-flex", alignItems: "center", gap: 4, marginLeft: 6, fontSize: 11, color: "var(--muted)" }}>
                      {React.cloneElement(Marks[e.connector] || Marks.openapi, { size: 11 })}
                      {e.connector}
                    </span>
                  </div>
                  {e.error && <div className="mono" style={{ fontSize: 11, color: "var(--red)", marginTop: 2 }}>{e.error}</div>}
                </td>
                <td><span className="badge badge-slate">{e.mode}</span></td>
                <td><StatusBadge s={e.status}/></td>
                <td className="mono" style={{ fontSize: 11.5, color: "var(--muted)", textAlign: "right" }}>{e.dur}ms</td>
                <td><button className="btn btn-ghost btn-sm" style={{ width: 24, padding: 0 }}>{Ic.chevR}</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

const Usage = () => {
  return (
    <div style={{ padding: 20, display: "flex", flexDirection: "column", gap: 14 }}>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12 }}>
        <KpiCard label="Executions this month" value="14,238" sub="of 250,000 included" trend="5.7% of quota"/>
        <KpiCard label="Searches this month" value="3,184" sub="of 50,000 included" trend="6.4% of quota"/>
        <KpiCard label="Embedding tokens" value="1.82M" sub="of 5.0M included" trend="36.4% of quota"/>
      </div>

      <div className="card" style={{ padding: 16 }}>
        <div style={{ display: "flex", alignItems: "center", marginBottom: 14 }}>
          <h3 style={{ fontSize: 13, fontWeight: 500, margin: 0 }}>Current month</h3>
          <span className="badge badge-slate" style={{ marginLeft: 8 }}>April 2026</span>
          <span style={{ marginLeft: "auto", fontSize: 11.5, color: "var(--muted)" }} className="mono">resets May 1</span>
        </div>
        <QuotaRow label="Executions" used={14238} cap={250000}/>
        <QuotaRow label="Searches" used={3184} cap={50000}/>
        <QuotaRow label="Embedding tokens" used={1820000} cap={5000000} unit="tok"/>
      </div>

      <div className="card">
        <div style={{ padding: "12px 16px", borderBottom: "1px solid var(--border)" }}>
          <h3 style={{ fontSize: 13, fontWeight: 500, margin: 0 }}>Daily executions — last 30 days</h3>
        </div>
        <div style={{ padding: 16, height: 200, display: "flex", alignItems: "flex-end", gap: 3 }}>
          {Array.from({ length: 30 }).map((_, i) => {
            const h = 25 + Math.sin(i * 0.7) * 30 + Math.random() * 50 + (i > 22 ? 30 : 0);
            return <div key={i} style={{ flex: 1, height: `${Math.min(95, h)}%`, background: i > 26 ? "var(--accent)" : "var(--ink-2)", borderRadius: 2, opacity: 0.85 }}/>;
          })}
        </div>
        <div style={{ padding: "0 16px 12px", display: "flex", justifyContent: "space-between", fontSize: 10.5, color: "var(--muted)" }} className="mono">
          <span>Apr 1</span><span>Apr 8</span><span>Apr 15</span><span>Apr 22</span><span>Apr 30</span>
        </div>
      </div>
    </div>
  );
};

window.SearchPlayground = SearchPlayground;
window.ApiKeys = ApiKeys;
window.Executions = Executions;
window.Usage = Usage;
