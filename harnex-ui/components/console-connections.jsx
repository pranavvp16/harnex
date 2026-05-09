// Connections list, New Connection wizard, Connection Detail
const ConnectionsList = ({ setPage, setOpenConn }) => {
  const [filter, setFilter] = React.useState("");
  const [statusFilter, setStatusFilter] = React.useState("all");
  const filtered = SampleConnections.filter(c =>
    (statusFilter === "all" || c.status === statusFilter) &&
    (filter === "" || c.name.includes(filter) || c.connectorName.toLowerCase().includes(filter.toLowerCase()))
  );

  const counts = {
    ready: SampleConnections.filter(c => c.status === "ready").length,
    indexing: SampleConnections.filter(c => c.status === "indexing").length,
    error: SampleConnections.filter(c => c.status === "error").length,
    disabled: SampleConnections.filter(c => c.status === "disabled").length,
  };

  return (
    <div style={{ padding: 20, display: "flex", flexDirection: "column", gap: 14 }}>
      {/* Status cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 10 }}>
        {[
          { k: "ready", label: "Ready", color: "green" },
          { k: "indexing", label: "Indexing", color: "amber" },
          { k: "error", label: "Errored", color: "red" },
          { k: "disabled", label: "Disabled", color: "slate" },
        ].map(s => (
          <button key={s.k} onClick={() => setStatusFilter(statusFilter === s.k ? "all" : s.k)} style={{ textAlign: "left", padding: 12, background: "var(--surface)", border: `1px solid ${statusFilter === s.k ? "var(--ink)" : "var(--border)"}`, borderRadius: 8, cursor: "pointer", display: "flex", alignItems: "center", gap: 10 }}>
            <span style={{ width: 8, height: 8, borderRadius: 999, background: `var(--${s.color === "slate" ? "muted" : s.color})` }}/>
            <span style={{ fontSize: 12, color: "var(--slate)" }}>{s.label}</span>
            <span className="h-display" style={{ marginLeft: "auto", fontSize: 22, fontWeight: 500 }}>{counts[s.k]}</span>
          </button>
        ))}
      </div>

      {/* Toolbar */}
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <div style={{ position: "relative", width: 280 }}>
          <span style={{ position: "absolute", left: 10, top: 9, color: "var(--muted)" }}>{Ic.search}</span>
          <input className="input" value={filter} onChange={e => setFilter(e.target.value)} placeholder="Filter connections" style={{ paddingLeft: 30 }}/>
        </div>
        <select className="select" style={{ width: 140 }} value={statusFilter} onChange={e => setStatusFilter(e.target.value)}>
          <option value="all">All statuses</option>
          <option value="ready">Ready</option>
          <option value="indexing">Indexing</option>
          <option value="error">Errored</option>
          <option value="disabled">Disabled</option>
        </select>
        <button className="btn btn-ghost btn-sm">{Ic.filter} Filters</button>
        <span style={{ marginLeft: "auto" }}/>
        <button className="btn btn-primary btn-sm" onClick={() => setPage("new-connection")}>{Ic.plus} New connection</button>
      </div>

      {/* Table */}
      <div className="card" style={{ overflow: "hidden" }}>
        <table className="tbl">
          <thead>
            <tr>
              <th style={{ width: 24 }}><input type="checkbox" style={{ accentColor: "var(--ink)" }}/></th>
              <th>Name</th>
              <th>Connector</th>
              <th>Mode</th>
              <th>Auth</th>
              <th style={{ textAlign: "right" }}>Endpoints</th>
              <th>Status</th>
              <th style={{ width: 120 }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map(c => (
              <tr key={c.id} className="row-hover" style={{ cursor: "pointer" }} onClick={() => { setOpenConn(c); setPage("connection-detail"); }}>
                <td><input type="checkbox" onClick={e => e.stopPropagation()} style={{ accentColor: "var(--ink)" }}/></td>
                <td>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <span style={{ display: "inline-flex" }}>{React.cloneElement(Marks[c.connector] || Marks.openapi, { size: 16 })}</span>
                    <span className="mono" style={{ fontSize: 12.5, fontWeight: 500 }}>{c.name}</span>
                  </div>
                </td>
                <td><span style={{ fontSize: 12.5, color: "var(--slate)" }}>{c.connectorName}</span></td>
                <td><span className="badge badge-slate">{c.mode}</span></td>
                <td><span style={{ fontSize: 12, color: "var(--slate)" }}>{c.auth}</span></td>
                <td className="mono" style={{ fontSize: 12, textAlign: "right", color: "var(--slate)" }}>{c.endpoints}</td>
                <td><StatusBadge s={c.status}/></td>
                <td>
                  <div style={{ display: "flex", gap: 4 }} onClick={e => e.stopPropagation()}>
                    <button className="btn btn-ghost btn-sm" title="Reindex">{Ic.refresh}</button>
                    <button className="btn btn-ghost btn-sm" title="More">{Ic.more}</button>
                    <button className="btn btn-ghost btn-sm" title="Delete" style={{ color: "var(--red)" }}>{Ic.trash}</button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

const NewConnection = ({ setPage }) => {
  const [step, setStep] = React.useState(1);
  const [picked, setPicked] = React.useState(null);
  const [name, setName] = React.useState("");
  const [authMethod, setAuthMethod] = React.useState("bearer");

  const tiles = [
    { id: "github", name: "GitHub", desc: "Connect GitHub orgs and repos. Auth via OAuth or PAT.", icon: Marks.github },
    { id: "jenkins", name: "Jenkins", desc: "Build, queue, and job APIs from a Jenkins controller.", icon: Marks.jenkins },
    { id: "openapi", name: "OpenAPI URL", desc: "Point to an OpenAPI 3.x JSON or YAML spec by URL.", icon: Marks.openapi },
    { id: "upload", name: "Upload OpenAPI", desc: "Upload an OpenAPI 3.x file from your machine.", icon: <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12"/></svg> },
    { id: "bareurl", name: "Bare API URL", desc: "Any HTTP API. Harnex probes paths and auth options.", icon: <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"><path d="M10 13a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-1 1"/><path d="M14 11a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l1-1"/></svg> },
  ];

  return (
    <div style={{ padding: 20, maxWidth: 880, margin: "0 auto", display: "flex", flexDirection: "column", gap: 16 }}>
      {/* Breadcrumb */}
      <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12 }}>
        <button className="btn btn-ghost btn-sm" onClick={() => setPage("connections")}>{Ic.back} Back</button>
        <span style={{ color: "var(--muted)" }}>Connections</span>
        <span style={{ color: "var(--muted)" }}>/</span>
        <span>New connection</span>
      </div>

      {/* Stepper */}
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        {[
          { n: 1, label: "Choose connector" },
          { n: 2, label: "Configure" },
          { n: 3, label: "Review" },
        ].map((s, i, arr) => (
          <React.Fragment key={s.n}>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{ width: 22, height: 22, borderRadius: 999, background: step >= s.n ? "var(--ink)" : "var(--surface)", color: step >= s.n ? "#fff" : "var(--muted)", border: step >= s.n ? "none" : "1px solid var(--border)", display: "inline-flex", alignItems: "center", justifyContent: "center", fontSize: 11, fontWeight: 500 }}>
                {step > s.n ? Ic.check : s.n}
              </span>
              <span style={{ fontSize: 12.5, color: step >= s.n ? "var(--ink)" : "var(--muted)", fontWeight: step === s.n ? 500 : 400 }}>{s.label}</span>
            </div>
            {i < arr.length - 1 && <span style={{ flex: 1, height: 1, background: "var(--border)", maxWidth: 80 }}/>}
          </React.Fragment>
        ))}
      </div>

      {step === 1 && (
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          <div>
            <h2 className="h-display" style={{ fontSize: 22, margin: "8px 0 4px", fontWeight: 500 }}>Choose a <span className="serif-i">connector</span></h2>
            <p style={{ fontSize: 13, color: "var(--slate)", margin: 0 }}>Pick a built-in connector or bring your own spec.</p>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
            {tiles.map(t => (
              <button key={t.id} onClick={() => setPicked(t.id)} style={{
                display: "flex", alignItems: "flex-start", gap: 14, padding: 16, textAlign: "left",
                border: `1px solid ${picked === t.id ? "var(--ink)" : "var(--border)"}`,
                borderRadius: 8, background: "var(--surface)", cursor: "pointer",
                boxShadow: picked === t.id ? "0 0 0 3px rgba(10,10,10,0.06)" : "none"
              }}>
                <div style={{ width: 44, height: 44, borderRadius: 6, background: "var(--bg-alt)", border: "1px solid var(--border)", display: "inline-flex", alignItems: "center", justifyContent: "center", color: "var(--ink)", flexShrink: 0 }}>
                  {React.cloneElement(t.icon, { size: 24 })}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 14, fontWeight: 500, marginBottom: 3 }}>{t.name}</div>
                  <div style={{ fontSize: 12, color: "var(--muted)", lineHeight: 1.5 }}>{t.desc}</div>
                </div>
                {picked === t.id && <span style={{ color: "var(--accent)" }}>{Ic.check}</span>}
              </button>
            ))}
          </div>
          <div style={{ display: "flex", justifyContent: "flex-end", marginTop: 8 }}>
            <button className="btn btn-primary" disabled={!picked} onClick={() => setStep(2)} style={{ opacity: picked ? 1 : 0.5 }}>
              Continue {Ic.arrow}
            </button>
          </div>
        </div>
      )}

      {step === 2 && (
        <div className="card" style={{ padding: 24, display: "flex", flexDirection: "column", gap: 16 }}>
          <div>
            <h2 className="h-display" style={{ fontSize: 22, margin: "0 0 4px", fontWeight: 500 }}>Configure <span className="serif-i">{tiles.find(t => t.id === picked)?.name}</span></h2>
            <p style={{ fontSize: 13, color: "var(--slate)", margin: 0 }}>Harnex will validate and index this connection.</p>
          </div>
          <Field label="Connection name" hint="Lowercase, dashes. Used in API responses.">
            <input className="input input-mono" value={name} onChange={e => setName(e.target.value)} placeholder="github-main"/>
          </Field>
          <Field label={picked === "openapi" || picked === "upload" ? "Spec URL" : "Base URL"} hint="Where Harnex should make calls.">
            <input className="input input-mono" placeholder={picked === "github" ? "https://api.github.com" : picked === "jenkins" ? "https://ci.example.com" : "https://api.example.com"}/>
          </Field>

          {picked === "upload" && (
            <Field label="OpenAPI file" hint="JSON or YAML, OpenAPI 3.x.">
              <div style={{ border: "1px dashed var(--border-strong)", borderRadius: 8, padding: 18, textAlign: "center", background: "var(--bg-alt)", cursor: "pointer" }}>
                <div style={{ display: "inline-flex", color: "var(--muted)", marginBottom: 6 }}>{Ic.upload}</div>
                <div style={{ fontSize: 13, color: "var(--slate)" }}>Drop a file here or <span style={{ color: "var(--accent)", fontWeight: 500 }}>browse</span></div>
              </div>
            </Field>
          )}

          <Field label="Auth method">
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 6 }}>
              {[
                { id: "none", label: "None" },
                { id: "header", label: "API key — header" },
                { id: "query", label: "API key — query" },
                { id: "bearer", label: "Bearer token" },
                { id: "basic", label: "Basic auth" },
                { id: "oauth", label: "OAuth — auth code" },
                { id: "client", label: "OAuth — client cred" },
              ].map(a => (
                <button key={a.id} onClick={() => setAuthMethod(a.id)} style={{
                  padding: "8px 10px", textAlign: "left",
                  border: `1px solid ${authMethod === a.id ? "var(--ink)" : "var(--border)"}`,
                  background: authMethod === a.id ? "var(--surface-2)" : "var(--surface)",
                  borderRadius: 6, fontSize: 12, cursor: "pointer", color: "var(--ink)"
                }}>{a.label}</button>
              ))}
            </div>
          </Field>

          {authMethod === "bearer" && (
            <Field label="Bearer token" hint="Stored in vault. Never displayed after save.">
              <input className="input input-mono" type="password" placeholder="ghp_••••••••••••••••••"/>
            </Field>
          )}
          {authMethod === "header" && (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 2fr", gap: 8 }}>
              <Field label="Header name"><input className="input input-mono" placeholder="X-API-Key"/></Field>
              <Field label="Header value"><input className="input input-mono" type="password" placeholder="••••••••"/></Field>
            </div>
          )}
          {authMethod === "basic" && (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
              <Field label="Username"><input className="input input-mono"/></Field>
              <Field label="Password"><input className="input input-mono" type="password"/></Field>
            </div>
          )}
          {authMethod === "oauth" && (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
              <Field label="Client ID"><input className="input input-mono"/></Field>
              <Field label="Client secret"><input className="input input-mono" type="password"/></Field>
              <Field label="Authorize URL"><input className="input input-mono" placeholder="https://example.com/oauth/authorize"/></Field>
              <Field label="Token URL"><input className="input input-mono" placeholder="https://example.com/oauth/token"/></Field>
            </div>
          )}

          <div style={{ display: "flex", gap: 8, marginTop: 6 }}>
            <button className="btn btn-ghost" onClick={() => setStep(1)}>{Ic.back} Back</button>
            <span style={{ flex: 1 }}/>
            <button className="btn btn-secondary">Test connection</button>
            <button className="btn btn-primary" onClick={() => setStep(3)}>Continue {Ic.arrow}</button>
          </div>
        </div>
      )}

      {step === 3 && (
        <div className="card" style={{ padding: 24, display: "flex", flexDirection: "column", gap: 14 }}>
          <h2 className="h-display" style={{ fontSize: 22, margin: 0, fontWeight: 500 }}>Review & <span className="serif-i">create</span></h2>
          <div style={{ background: "var(--bg-alt)", border: "1px solid var(--border)", borderRadius: 6, padding: 14, fontSize: 12.5, fontFamily: "var(--font-mono)" }}>
            <div style={{ display: "grid", gridTemplateColumns: "140px 1fr", rowGap: 6 }}>
              <span style={{ color: "var(--muted)" }}>connector</span><span>{tiles.find(t => t.id === picked)?.name}</span>
              <span style={{ color: "var(--muted)" }}>name</span><span>{name || "—"}</span>
              <span style={{ color: "var(--muted)" }}>auth</span><span>{authMethod}</span>
              <span style={{ color: "var(--muted)" }}>indexing</span><span style={{ color: "var(--accent)" }}>queued</span>
            </div>
          </div>
          <div className="alert alert-info">
            <span style={{ display: "inline-flex" }}>{Ic.info}</span>
            Harnex will start indexing immediately. Most APIs are fully indexed within 60 seconds.
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <button className="btn btn-ghost" onClick={() => setStep(2)}>{Ic.back} Back</button>
            <span style={{ flex: 1 }}/>
            <button className="btn btn-accent" onClick={() => setPage("connections")}>Create connection</button>
          </div>
        </div>
      )}
    </div>
  );
};

const Field = ({ label, hint, children }) => (
  <div style={{ display: "flex", flexDirection: "column", gap: 5 }}>
    <label style={{ fontSize: 12, fontWeight: 500 }}>{label}</label>
    {children}
    {hint && <span style={{ fontSize: 11, color: "var(--muted)" }}>{hint}</span>}
  </div>
);

const ConnectionDetail = ({ conn, setPage }) => {
  const c = conn || SampleConnections[0];
  return (
    <div style={{ padding: 20, display: "flex", flexDirection: "column", gap: 14 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, marginBottom: 4 }}>
        <button className="btn btn-ghost btn-sm" onClick={() => setPage("connections")}>{Ic.back} Back</button>
        <span style={{ color: "var(--muted)" }}>Connections</span>
        <span style={{ color: "var(--muted)" }}>/</span>
        <span className="mono">{c.name}</span>
      </div>

      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <div style={{ width: 44, height: 44, borderRadius: 8, background: "var(--surface)", border: "1px solid var(--border)", display: "inline-flex", alignItems: "center", justifyContent: "center", color: "var(--ink)" }}>
          {React.cloneElement(Marks[c.connector] || Marks.openapi, { size: 24 })}
        </div>
        <div>
          <h2 style={{ fontSize: 20, fontWeight: 500, margin: 0, letterSpacing: "-0.01em" }} className="mono">{c.name}</h2>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 4 }}>
            <StatusBadge s={c.status}/>
            <span style={{ fontSize: 12, color: "var(--muted)" }}>{c.connectorName} · {c.endpoints} operations indexed</span>
          </div>
        </div>
        <span style={{ flex: 1 }}/>
        <button className="btn btn-secondary btn-sm">{Ic.refresh} Reindex</button>
        <button className="btn btn-ghost btn-sm">{Ic.eye} View ops</button>
        <button className="btn btn-danger btn-sm">{Ic.trash} Delete</button>
      </div>

      {c.status === "error" && c.lastError && (
        <div className="alert alert-red">
          <span style={{ display: "inline-flex" }}>{Ic.warning}</span>
          <div>
            <strong>Indexing failed.</strong>
            <div className="mono" style={{ fontSize: 12, marginTop: 3 }}>{c.lastError}</div>
          </div>
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
        {/* Overview */}
        <div className="card">
          <div style={{ padding: "12px 16px", borderBottom: "1px solid var(--border)" }}>
            <h3 style={{ fontSize: 13, fontWeight: 500, margin: 0 }}>Overview</h3>
          </div>
          <div style={{ padding: 16 }}>
            <KeyVal k="Connector" v={c.connectorName}/>
            <KeyVal k="Mode" v={<span className="badge badge-slate">{c.mode}</span>}/>
            <KeyVal k="Auth flow" v={c.auth}/>
            <KeyVal k="Endpoints indexed" v={<span className="mono">{c.endpoints}</span>}/>
            <KeyVal k="Base URL" v={<span className="mono" style={{ fontSize: 12 }}>{c.baseUrl}</span>}/>
            <KeyVal k="Last indexed" v={<span className="mono" style={{ fontSize: 12 }}>{c.lastIndexed}</span>}/>
            <KeyVal k="Created" v={<span className="mono" style={{ fontSize: 12 }}>{c.created}</span>} last/>
          </div>
        </div>

        {/* Auth + Identifiers */}
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <div className="card">
            <div style={{ padding: "12px 16px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", gap: 6 }}>
              <h3 style={{ fontSize: 13, fontWeight: 500, margin: 0 }}>Auth configuration</h3>
              <span className="badge badge-slate" style={{ height: 18, fontSize: 10 }}>{Ic.lock} public shape only</span>
            </div>
            <div style={{ padding: 16 }}>
              <KeyVal k="Method" v={c.auth}/>
              <KeyVal k="Header name" v={<span className="mono" style={{ fontSize: 12 }}>Authorization</span>}/>
              <KeyVal k="Token prefix" v={<span className="mono" style={{ fontSize: 12 }}>Bearer ••••</span>}/>
              <KeyVal k="Stored in" v={<span style={{ display: "inline-flex", alignItems: "center", gap: 4, color: "var(--accent-ink)" }}>{Ic.lock} vault</span>} last/>
            </div>
          </div>

          <div className="card">
            <div style={{ padding: "12px 16px", borderBottom: "1px solid var(--border)" }}>
              <h3 style={{ fontSize: 13, fontWeight: 500, margin: 0 }}>Identifiers</h3>
            </div>
            <div style={{ padding: 16 }}>
              <KeyVal k="Connection ID" v={<span className="mono" style={{ fontSize: 12 }}>{c.id}</span>}/>
              <KeyVal k="Tenant ID" v={<span className="mono" style={{ fontSize: 12 }}>tn_acmecorp</span>} last/>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const KeyVal = ({ k, v, last }) => (
  <div style={{ display: "grid", gridTemplateColumns: "140px 1fr", padding: "8px 0", borderBottom: last ? "none" : "1px solid var(--border-soft)", alignItems: "center" }}>
    <span style={{ fontSize: 12, color: "var(--muted)" }}>{k}</span>
    <span style={{ fontSize: 12.5 }}>{v}</span>
  </div>
);

window.ConnectionsList = ConnectionsList;
window.NewConnection = NewConnection;
window.ConnectionDetail = ConnectionDetail;
