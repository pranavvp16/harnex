// Marketing Landing Page
const Marketing = ({ onEnterConsole }) => {
  return (
    <div style={{ background: "transparent", color: "var(--ink)", minHeight: "100%", overflow: "auto", height: "100%", position: "relative", zIndex: 1 }}>
      <MktNav onEnterConsole={onEnterConsole} />
      <MktHero onEnterConsole={onEnterConsole} />
      <MktMarquee />
      <MktFeatures />
      <MktHowItWorks />
      <MktUseCases />
      <MktSecurity />
      <MktPricing onEnterConsole={onEnterConsole} />
      <MktFooter />
    </div>
  );
};

const MktNav = ({ onEnterConsole }) => (
  <header style={{
    position: "sticky", top: 0, zIndex: 30,
    background: "color-mix(in srgb, var(--bg) 82%, transparent)", backdropFilter: "saturate(180%) blur(8px)",
    WebkitBackdropFilter: "saturate(180%) blur(8px)",
    borderBottom: "1px solid var(--border)",
  }}>
    <div style={{ maxWidth: 1200, margin: "0 auto", padding: "12px 32px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 36 }}>
        <HarnexLogo size={22} />
        <nav style={{ display: "flex", gap: 24, fontSize: 13.5, color: "var(--slate)" }}>
          <a href="#features">Product</a>
          <a href="#how">How it works</a>
          <a href="#use-cases">Use cases</a>
          <a href="#security">Security</a>
          <a href="#pricing">Pricing</a>
          <a href="#docs">Docs</a>
        </nav>
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <button className="btn btn-ghost btn-sm" onClick={onEnterConsole}>Sign in</button>
        <button className="btn btn-primary btn-sm" onClick={onEnterConsole}>Get started <span style={{ display: "inline-flex" }}>{Ic.arrow}</span></button>
      </div>
    </div>
  </header>
);

const MktHero = ({ onEnterConsole }) => (
  <section style={{ maxWidth: 1200, margin: "0 auto", padding: "80px 32px 60px" }}>
    <div style={{ display: "inline-flex", alignItems: "center", gap: 6, padding: "5px 10px", border: "1px solid var(--border)", borderRadius: 999, background: "var(--surface)", fontSize: 12, color: "var(--slate)", marginBottom: 32 }}>
      <span style={{ width: 6, height: 6, borderRadius: 999, background: "var(--accent)" }}/>
      <span>MCP-native API connector platform</span>
      <span style={{ color: "var(--muted)" }}>·</span>
      <span style={{ color: "var(--muted)" }}>YC W26</span>
    </div>
    <h1 className="h-display" style={{ fontSize: 80, margin: "0 0 28px", maxWidth: 1000, fontWeight: 500 }}>
      Connect <span className="serif-i" style={{ color: "var(--ink)" }}>every</span> API<br/>
      to your <span className="serif-i">agents</span>.
    </h1>
    <p style={{ fontSize: 19, color: "var(--slate)", maxWidth: 640, margin: "0 0 36px", lineHeight: 1.5 }}>
      Harnex indexes your HTTP APIs, makes operations searchable, and exposes secure search + execute tools through MCP.
    </p>
    <div style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: 60 }}>
      <button className="btn btn-primary btn-lg" onClick={onEnterConsole}>
        Get started {Ic.arrow}
      </button>
      <button className="btn btn-ghost btn-lg">
        {Ic.book} View docs
      </button>
      <span style={{ marginLeft: 12, fontSize: 13, color: "var(--muted)" }}>
        <span className="mono" style={{ background: "var(--surface)", border: "1px solid var(--border)", padding: "3px 6px", borderRadius: 4, fontSize: 11.5 }}>npm i @harnex/mcp</span>
      </span>
    </div>

    <HeroProductShot />
  </section>
);

const HeroProductShot = () => (
  <div style={{
    border: "1px solid var(--border)", borderRadius: 12, background: "var(--surface)",
    boxShadow: "var(--shadow-lg)", overflow: "hidden", position: "relative"
  }}>
    {/* Window chrome */}
    <div style={{ display: "flex", alignItems: "center", padding: "10px 14px", borderBottom: "1px solid var(--border)", background: "var(--surface-2)" }}>
      <div style={{ display: "flex", gap: 6 }}>
        <span style={{ width: 11, height: 11, borderRadius: 999, background: "#E5E5E0", border: "1px solid var(--border)" }}/>
        <span style={{ width: 11, height: 11, borderRadius: 999, background: "#E5E5E0", border: "1px solid var(--border)" }}/>
        <span style={{ width: 11, height: 11, borderRadius: 999, background: "#E5E5E0", border: "1px solid var(--border)" }}/>
      </div>
      <div style={{ flex: 1, textAlign: "center", fontSize: 12, color: "var(--muted)" }} className="mono">app.harnex.dev/search</div>
      <div style={{ width: 40 }}/>
    </div>

    <div style={{ display: "grid", gridTemplateColumns: "200px 1fr 320px", height: 480 }}>
      {/* Sidebar */}
      <div style={{ borderRight: "1px solid var(--border)", padding: 12, background: "var(--surface-2)", fontSize: 12.5 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "5px 8px", borderRadius: 6, color: "var(--muted)" }}>{Ic.home} Dashboard</div>
        <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "5px 8px", borderRadius: 6, color: "var(--muted)" }}>{Ic.plug} Connections</div>
        <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "5px 8px", borderRadius: 6, background: "var(--surface)", border: "1px solid var(--border)", color: "var(--ink)", fontWeight: 500 }}>{Ic.searchNav} Search</div>
        <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "5px 8px", borderRadius: 6, color: "var(--muted)" }}>{Ic.key} API Keys</div>
        <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "5px 8px", borderRadius: 6, color: "var(--muted)" }}>{Ic.zap} Executions</div>
        <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "5px 8px", borderRadius: 6, color: "var(--muted)" }}>{Ic.bar} Usage</div>
        <div style={{ marginTop: 24, fontSize: 10.5, color: "var(--muted)", textTransform: "uppercase", letterSpacing: "0.06em", padding: "0 8px 6px" }}>Connections</div>
        {[
          { name: "github-main", c: "github", n: "GitHub", s: "ready" },
          { name: "stripe-prod", c: "stripe", n: "Stripe", s: "ready" },
          { name: "linear-eng", c: "linear", n: "Linear", s: "ready" },
          { name: "datadog-obs", c: "datadog", n: "Datadog", s: "ready" },
          { name: "jenkins-ci", c: "jenkins", n: "Jenkins", s: "indexing" },
        ].map(x => (
          <div key={x.name} style={{ display: "flex", alignItems: "center", gap: 8, padding: "4px 8px", color: "var(--slate)", fontSize: 12 }}>
            <span style={{ display: "inline-flex", color: "var(--ink)" }}>{React.cloneElement(Marks[x.c], { size: 14 })}</span>
            <span className="mono" style={{ fontSize: 11 }}>{x.name}</span>
            <span style={{ marginLeft: "auto", width: 6, height: 6, borderRadius: 999, background: x.s === "ready" ? "var(--green)" : "var(--amber)" }}/>
          </div>
        ))}
      </div>

      {/* Center: search */}
      <div style={{ padding: 18, display: "flex", flexDirection: "column", gap: 12 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span className="kicker">Search Playground</span>
          <span style={{ marginLeft: "auto", fontSize: 11.5, color: "var(--muted)" }} className="mono">top_k=5</span>
        </div>
        <div style={{ position: "relative" }}>
          <span style={{ position: "absolute", left: 12, top: 10, color: "var(--muted)" }}>{Ic.search}</span>
          <input className="input" defaultValue="list pull requests for repo" style={{ height: 40, paddingLeft: 34, fontSize: 14, background: "var(--surface)" }}/>
          <span className="mono" style={{ position: "absolute", right: 10, top: 11, fontSize: 11, color: "var(--muted)", border: "1px solid var(--border)", padding: "2px 5px", borderRadius: 4 }}>⌘K</span>
        </div>

        {[
          { m: "GET", p: "/repos/{owner}/{repo}/pulls", s: "List pull requests for a repository", c: "github", cn: "GitHub", id: "pulls/list", sc: 0.94 },
          { m: "GET", p: "/repos/{owner}/{repo}/pulls/{pull_number}", s: "Get a pull request by number", c: "github", cn: "GitHub", id: "pulls/get", sc: 0.88 },
          { m: "POST", p: "/repos/{owner}/{repo}/pulls", s: "Create a new pull request", c: "github", cn: "GitHub", id: "pulls/create", sc: 0.82 },
          { m: "GET", p: "/api/v1/issues", s: "List issues across teams", c: "linear", cn: "Linear", id: "issues.list", sc: 0.62 },
        ].map((r, i) => (
          <div key={i} style={{ border: "1px solid var(--border)", borderRadius: 8, padding: "10px 12px", background: i === 0 ? "var(--accent-soft)" : "var(--surface)", borderColor: i === 0 ? "var(--accent-border)" : "var(--border)" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span className={`method method-${r.m.toLowerCase()}`}>{r.m}</span>
              <span className="mono" style={{ fontSize: 12, color: "var(--ink)", fontWeight: 500 }}>{r.p}</span>
              <span style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 6, fontSize: 11, color: "var(--muted)" }}>
                <span style={{ display: "inline-flex", color: "var(--ink)" }}>{React.cloneElement(Marks[r.c], { size: 12 })}</span>
                {r.cn}
                <span className="mono" style={{ background: i === 0 ? "rgba(154,52,18,0.1)" : "var(--bg-alt)", padding: "1px 5px", borderRadius: 3, color: i === 0 ? "var(--accent-ink)" : "var(--slate)", fontWeight: 500 }}>{r.sc.toFixed(2)}</span>
              </span>
            </div>
            <div style={{ fontSize: 12, color: "var(--slate)", marginTop: 4 }}>{r.s}</div>
            <div className="mono" style={{ fontSize: 10.5, color: "var(--muted)", marginTop: 2 }}>op: {r.id}</div>
          </div>
        ))}
      </div>

      {/* Right: execution log */}
      <div style={{ borderLeft: "1px solid var(--border)", background: "var(--surface-2)", padding: 18, display: "flex", flexDirection: "column", gap: 10, fontSize: 12 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span className="kicker">Recent Executions</span>
          <span style={{ marginLeft: "auto", display: "inline-flex", alignItems: "center", gap: 4, fontSize: 11, color: "var(--green)" }}>
            <span style={{ width: 6, height: 6, borderRadius: 999, background: "var(--green)" }}/>live
          </span>
        </div>
        {[
          { t: "14:32:11", m: "GET", p: "/repos/{owner}/{repo}/pulls", s: "ok", d: "184ms" },
          { t: "14:31:48", m: "POST", p: "/v1/charges", s: "ok", d: "312ms" },
          { t: "14:30:09", m: "GET", p: "/api/v1/issues", s: "ok", d: "96ms" },
          { t: "14:28:55", m: "POST", p: "/api/v2/events", s: "ok", d: "142ms" },
          { t: "14:27:21", m: "GET", p: "/repos/{owner}/{repo}/issues", s: "err", d: "5012ms" },
          { t: "14:25:03", m: "POST", p: "/chat.postMessage", s: "ok", d: "221ms" },
          { t: "14:23:44", m: "DEL", p: "/v1/customers/{id}", s: "ok", d: "178ms" },
          { t: "14:22:11", m: "GET", p: "/api/v1/teams", s: "ok", d: "87ms" },
        ].map((e, i) => (
          <div key={i} style={{ display: "flex", alignItems: "center", gap: 8, padding: "6px 0", borderBottom: i < 7 ? "1px solid var(--border-soft)" : "none" }}>
            <span className="mono" style={{ fontSize: 10.5, color: "var(--muted)" }}>{e.t}</span>
            <span className={`method method-${e.m === "DEL" ? "delete" : e.m.toLowerCase()}`} style={{ fontSize: 9.5 }}>{e.m}</span>
            <span className="mono" style={{ fontSize: 10.5, color: "var(--ink)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", flex: 1 }}>{e.p}</span>
            <span style={{ width: 6, height: 6, borderRadius: 999, background: e.s === "ok" ? "var(--green)" : "var(--red)" }}/>
            <span className="mono" style={{ fontSize: 10, color: "var(--muted)", width: 50, textAlign: "right" }}>{e.d}</span>
          </div>
        ))}
      </div>
    </div>
  </div>
);

const MARQUEE_LIST = [
  ["github","GitHub"],["gitlab","GitLab"],["bitbucket","Bitbucket"],["azuredevops","Azure DevOps"],
  ["jenkins","Jenkins"],["circleci","CircleCI"],["ghactions","GitHub Actions"],["buildkite","Buildkite"],
  ["argocd","Argo CD"],["spinnaker","Spinnaker"],
  ["jira","Jira"],["linear","Linear"],["asana","Asana"],["trello","Trello"],["clickup","ClickUp"],["notion","Notion"],["monday","Monday"],
  ["datadog","Datadog"],["newrelic","New Relic"],["grafana","Grafana"],["prometheus","Prometheus"],["sentry","Sentry"],["honeycomb","Honeycomb"],["pagerduty","PagerDuty"],["opsgenie","Opsgenie"],
  ["aws","AWS"],["gcp","Google Cloud"],["azure","Azure"],["cloudflare","Cloudflare"],["vercel","Vercel"],["netlify","Netlify"],["heroku","Heroku"],["render","Render"],["railway","Railway"],["flyio","Fly.io"],["kubernetes","Kubernetes"],["docker","Docker"],["terraform","Terraform"],["pulumi","Pulumi"],
  ["postgres","PostgreSQL"],["mysql","MySQL"],["mongodb","MongoDB"],["redis","Redis"],["snowflake","Snowflake"],["bigquery","BigQuery"],["databricks","Databricks"],["supabase","Supabase"],["neon","Neon"],["planetscale","PlanetScale"],["elasticsearch","Elastic"],
  ["slack","Slack"],["discord","Discord"],["msteams","MS Teams"],["gmail","Gmail"],["outlook","Outlook"],["twilio","Twilio"],["sendgrid","SendGrid"],
  ["confluence","Confluence"],["gdrive","Google Drive"],["dropbox","Dropbox"],["box","Box"],["readme","ReadMe"],["gitbook","GitBook"],["mintlify","Mintlify"],["openapi","OpenAPI"],["swagger","Swagger"],
  ["stripe","Stripe"],["plaid","Plaid"],["shopify","Shopify"],["hubspot","HubSpot"],["salesforce","Salesforce"],["zendesk","Zendesk"],["intercom","Intercom"],
  ["openai","OpenAI"],["anthropic","Anthropic"],["cohere","Cohere"],["langchain","LangChain"],["llamaindex","LlamaIndex"],["pinecone","Pinecone"],["weaviate","Weaviate"],["chroma","Chroma"],
];

const MktMarquee = () => {
  // Split into 2 rows for variety
  const half = Math.ceil(MARQUEE_LIST.length / 2);
  const row1 = MARQUEE_LIST.slice(0, half);
  const row2 = MARQUEE_LIST.slice(half);
  return (
    <section style={{ borderTop: "1px solid var(--border)", borderBottom: "1px solid var(--border)", padding: "48px 0", background: "var(--bg-alt)" }}>
      <div style={{ textAlign: "center", marginBottom: 28 }}>
        <h2 className="h-display" style={{ fontSize: 22, margin: 0, color: "var(--slate)", fontWeight: 500 }}>
          Works with the tools your team <span className="serif-i" style={{ color: "var(--ink)" }}>already</span> uses
        </h2>
      </div>
      <MarqueeRow items={row1} dir="left" speed={60}/>
      <div style={{ height: 12 }}/>
      <MarqueeRow items={row2} dir="right" speed={75}/>
    </section>
  );
};

const MarqueeRow = ({ items, dir = "left", speed = 60 }) => {
  // Duplicate for infinite scroll
  const tripled = [...items, ...items, ...items];
  const dur = `${speed}s`;
  return (
    <div style={{ position: "relative", overflow: "hidden", maskImage: "linear-gradient(to right, transparent, black 8%, black 92%, transparent)", WebkitMaskImage: "linear-gradient(to right, transparent, black 8%, black 92%, transparent)" }}>
      <div style={{
        display: "flex", gap: 10,
        animation: `${dir === "left" ? "marqueeL" : "marqueeR"} ${dur} linear infinite`,
        width: "max-content"
      }}>
        {tripled.map(([k, n], i) => (
          <ConnectorCell key={`${k}-${i}`} name={n} mark={Marks[k]}/>
        ))}
      </div>
      <style>{`
        @keyframes marqueeL { from { transform: translateX(0); } to { transform: translateX(-33.333%); } }
        @keyframes marqueeR { from { transform: translateX(-33.333%); } to { transform: translateX(0); } }
      `}</style>
    </div>
  );
};

const MktFeatures = () => {
  const items = [
    { kicker: "Connect", title: "Connect any HTTP API", body: "GitHub, Jenkins, OpenAPI URL, OpenAPI upload, bare URL — or anything that speaks HTTP. Six built-in modes, hundreds more by spec.", visual: "connect" },
    { kicker: "Index", title: "Semantic search across operations", body: "Find the right operation in natural language. Harnex embeds every endpoint summary, parameter, and response shape so agents don't guess.", visual: "search" },
    { kicker: "Execute", title: "Structured, safe execution", body: "Agents call APIs through a typed envelope. Path parameters validated, request bodies coerced, errors returned as data — never as silent failures.", visual: "execute" },
    { kicker: "Secure", title: "Secrets never touch the console", body: "Credentials live in an isolated vault. Tokens are issued at execution time, scoped per-tenant, and never round-trip through the UI.", visual: "secure" },
    { kicker: "Multitenant", title: "Org-aware from day one", body: "Tenants, members, roles, quotas, API keys, usage. Built for platforms that need to map their customers to Harnex without forking.", visual: "multitenant" },
    { kicker: "MCP-native", title: "One server. Two tools.", body: "Drop the Harnex MCP server into Claude Desktop, Cursor, or any agent runtime. Agents only need search and execute.", visual: "mcp" },
  ];
  return (
    <section id="features" style={{ maxWidth: 1200, margin: "0 auto", padding: "100px 32px" }}>
      <div style={{ marginBottom: 48 }}>
        <span className="kicker">Features</span>
        <h2 className="h-display" style={{ fontSize: 48, margin: "12px 0 0", maxWidth: 720, fontWeight: 500 }}>
          One MCP server <span className="serif-i">for every API</span> your agents need.
        </h2>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16 }}>
        {items.map((f, i) => (
          <div key={i} className="card" style={{ padding: 24, display: "flex", flexDirection: "column", gap: 14, minHeight: 280 }}>
            <FeatureVisual kind={f.visual}/>
            <div>
              <div className="kicker" style={{ marginBottom: 6 }}>{f.kicker}</div>
              <h3 style={{ fontSize: 18, fontWeight: 500, margin: "0 0 6px", letterSpacing: "-0.01em" }}>{f.title}</h3>
              <p style={{ fontSize: 13.5, color: "var(--slate)", margin: 0, lineHeight: 1.5 }}>{f.body}</p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
};

const FeatureVisual = ({ kind }) => {
  const base = { height: 110, borderRadius: 6, background: "var(--surface-2)", border: "1px solid var(--border)", padding: 12, display: "flex", flexDirection: "column", gap: 6, fontSize: 11.5, fontFamily: "var(--font-mono)", color: "var(--slate)", overflow: "hidden" };
  if (kind === "connect") return (
    <div style={base}>
      {["GitHub","Stripe","OpenAPI URL","Bare URL"].map((x, i) => (
        <div key={i} style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <span style={{ width: 6, height: 6, borderRadius: 999, background: "var(--accent)" }}/>
          <span style={{ color: "var(--ink)" }}>{x}</span>
          <span style={{ marginLeft: "auto", color: "var(--muted)", fontSize: 10 }}>connected</span>
        </div>
      ))}
    </div>
  );
  if (kind === "search") return (
    <div style={base}>
      <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
        <span style={{ color: "var(--muted)" }}>{Ic.search}</span>
        <span style={{ color: "var(--ink)" }}>"create a customer"</span>
      </div>
      <div style={{ height: 1, background: "var(--border)", margin: "2px 0" }}/>
      {["POST /v1/customers · 0.93","POST /api/users · 0.71","POST /accounts · 0.62"].map((r, i) => (
        <div key={i} style={{ color: i === 0 ? "var(--ink)" : "var(--slate)" }}>{r}</div>
      ))}
    </div>
  );
  if (kind === "execute") return (
    <div style={base}>
      <div style={{ color: "var(--muted)" }}>{">"} harnex.execute(</div>
      <div style={{ paddingLeft: 12 }}>op: <span style={{ color: "var(--ink)" }}>"pulls/list"</span>,</div>
      <div style={{ paddingLeft: 12 }}>params: {"{ owner: \"acme\" }"}</div>
      <div style={{ color: "var(--muted)" }}>) → <span style={{ color: "var(--green)" }}>200 OK</span> · 184ms</div>
    </div>
  );
  if (kind === "secure") return (
    <div style={{ ...base, justifyContent: "center", alignItems: "center" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
        <div style={{ display: "flex", flexDirection: "column", gap: 4, alignItems: "center" }}>
          <span style={{ color: "var(--muted)", fontSize: 10 }}>console</span>
          <div style={{ width: 50, height: 30, border: "1px solid var(--border)", borderRadius: 4, background: "var(--surface)" }}/>
        </div>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", color: "var(--accent)" }}>
          {Ic.lock}
          <span style={{ fontSize: 9, color: "var(--muted)", marginTop: 2 }}>vault</span>
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 4, alignItems: "center" }}>
          <span style={{ color: "var(--muted)", fontSize: 10 }}>upstream</span>
          <div style={{ width: 50, height: 30, border: "1px solid var(--border)", borderRadius: 4, background: "var(--surface)" }}/>
        </div>
      </div>
    </div>
  );
  if (kind === "multitenant") return (
    <div style={base}>
      {[
        { t: "acme-corp", c: 12, q: 78 },
        { t: "globex", c: 7, q: 41 },
        { t: "soylent", c: 23, q: 92 },
      ].map((r, i) => (
        <div key={i} style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <span style={{ color: "var(--ink)", width: 90 }}>{r.t}</span>
          <span style={{ color: "var(--muted)", width: 60 }}>{r.c} conns</span>
          <div style={{ flex: 1, height: 4, background: "var(--border)", borderRadius: 2, overflow: "hidden" }}>
            <div style={{ width: `${r.q}%`, height: "100%", background: r.q > 80 ? "var(--accent)" : "var(--ink)" }}/>
          </div>
          <span style={{ color: "var(--muted)", fontSize: 10, width: 30, textAlign: "right" }}>{r.q}%</span>
        </div>
      ))}
    </div>
  );
  if (kind === "mcp") return (
    <div style={base}>
      <div style={{ color: "var(--muted)" }}>// mcp.json</div>
      <div>{"\""}harnex{"\""}:</div>
      <div style={{ paddingLeft: 8 }}>command: <span style={{ color: "var(--ink)" }}>"npx"</span>,</div>
      <div style={{ paddingLeft: 8 }}>args: [<span style={{ color: "var(--accent)" }}>"@harnex/mcp"</span>],</div>
      <div style={{ paddingLeft: 8 }}>tools: [<span style={{ color: "var(--ink)" }}>"search"</span>, <span style={{ color: "var(--ink)" }}>"execute"</span>]</div>
    </div>
  );
};

const MktHowItWorks = () => {
  const steps = [
    { n: "01", title: "Connect", body: "Add an API using a built-in connector, an OpenAPI spec, or a bare URL. Auth flows for Bearer, OAuth, basic, and headers are first-class." },
    { n: "02", title: "Index", body: "Harnex parses operations, embeds summaries and shapes, and verifies the connection is healthy. Indexing is incremental and reactive to spec changes." },
    { n: "03", title: "Search", body: "Agents query in natural language. Harnex returns ranked operations with method, path, summary, and operation id — never raw spec dumps." },
    { n: "04", title: "Execute", body: "Agents call one MCP tool: execute. Harnex validates params, injects credentials from the vault, and returns structured responses." },
  ];
  return (
    <section id="how" style={{ borderTop: "1px solid var(--border)", background: "var(--bg-alt)" }}>
      <div style={{ maxWidth: 1200, margin: "0 auto", padding: "100px 32px" }}>
        <div style={{ marginBottom: 48 }}>
          <span className="kicker">How it works</span>
          <h2 className="h-display" style={{ fontSize: 48, margin: "12px 0 0", maxWidth: 720, fontWeight: 500 }}>
            From spec to <span className="serif-i">agent-ready</span> in four steps.
          </h2>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 0, border: "1px solid var(--border)", borderRadius: 12, background: "var(--surface)", overflow: "hidden" }}>
          {steps.map((s, i) => (
            <div key={s.n} style={{ padding: 28, borderRight: i < 3 ? "1px solid var(--border)" : "none", display: "flex", flexDirection: "column", gap: 12, minHeight: 240 }}>
              <div style={{ display: "flex", alignItems: "baseline", gap: 8 }}>
                <span className="mono" style={{ fontSize: 11, color: "var(--accent)", fontWeight: 600 }}>{s.n}</span>
                <span style={{ flex: 1, height: 1, background: "var(--border)" }}/>
              </div>
              <h3 style={{ fontSize: 22, fontWeight: 500, margin: "0", letterSpacing: "-0.01em" }} className="h-display">{s.title}</h3>
              <p style={{ fontSize: 13.5, color: "var(--slate)", margin: 0, lineHeight: 1.5 }}>{s.body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

const MktUseCases = () => {
  const cases = [
    { tag: "Devtools", title: "Internal developer agents", body: "Agents that ship code, triage incidents, run pipelines, and update tickets — without each tool needing a custom integration.", details: ["GitHub PRs","Jenkins builds","Linear tickets","Datadog alerts"] },
    { tag: "Customer support", title: "Tier-1 support copilots", body: "Resolve issues by reading orders, refunding charges, posting Slack updates, and creating tickets — all from one MCP server.", details: ["Stripe refunds","Zendesk tickets","Slack updates","Internal billing"] },
    { tag: "Platform", title: "Embedded agents in your product", body: "Ship an agent feature without rebuilding integrations. Harnex multitenancy maps your customers' connections cleanly into yours.", details: ["Per-tenant auth","Quotas","API keys","Usage telemetry"] },
  ];
  return (
    <section id="use-cases" style={{ maxWidth: 1200, margin: "0 auto", padding: "100px 32px" }}>
      <div style={{ marginBottom: 48 }}>
        <span className="kicker">Use cases</span>
        <h2 className="h-display" style={{ fontSize: 48, margin: "12px 0 0", maxWidth: 720, fontWeight: 500 }}>
          Built for teams shipping <span className="serif-i">real</span> agents.
        </h2>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16 }}>
        {cases.map((c, i) => (
          <div key={i} className="card" style={{ padding: 28, display: "flex", flexDirection: "column", gap: 16 }}>
            <span className="badge badge-slate" style={{ alignSelf: "flex-start" }}>{c.tag}</span>
            <h3 style={{ fontSize: 22, fontWeight: 500, margin: 0, letterSpacing: "-0.01em" }} className="h-display">{c.title}</h3>
            <p style={{ fontSize: 13.5, color: "var(--slate)", margin: 0, lineHeight: 1.5 }}>{c.body}</p>
            <div style={{ borderTop: "1px solid var(--border-soft)", paddingTop: 14, display: "flex", flexDirection: "column", gap: 6 }}>
              {c.details.map(d => (
                <div key={d} style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 12.5, color: "var(--slate)" }}>
                  <span style={{ color: "var(--accent)" }}>{Ic.check}</span>
                  {d}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
};

const MktSecurity = () => (
  <section id="security" style={{ borderTop: "1px solid var(--border)", background: "var(--bg-alt)" }}>
    <div style={{ maxWidth: 1200, margin: "0 auto", padding: "100px 32px", display: "grid", gridTemplateColumns: "1fr 1fr", gap: 48 }}>
      <div>
        <span className="kicker">Security</span>
        <h2 className="h-display" style={{ fontSize: 48, margin: "12px 0 24px", fontWeight: 500 }}>
          Credentials <span className="serif-i">never</span><br/>round-trip through the UI.
        </h2>
        <p style={{ fontSize: 16, color: "var(--slate)", lineHeight: 1.6, maxWidth: 480 }}>
          Tokens, API keys, and OAuth refresh material live in an isolated vault. Harnex injects them only at execution time, scoped to the tenant, and never logs them in the console.
        </p>
        <div style={{ display: "flex", gap: 12, marginTop: 28, flexWrap: "wrap" }}>
          {["SOC 2 Type II","HIPAA-ready","Self-hosted vault","Tenant isolation","Audit logs"].map(b => (
            <span key={b} className="badge badge-slate" style={{ height: 24, fontSize: 12 }}>{Ic.shield}<span style={{ marginLeft: 4 }}>{b}</span></span>
          ))}
        </div>
      </div>
      <div className="card" style={{ padding: 0, overflow: "hidden", alignSelf: "start" }}>
        <div style={{ padding: "10px 14px", borderBottom: "1px solid var(--border)", background: "var(--surface-2)", display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ color: "var(--accent)" }}>{Ic.lock}</span>
          <span className="mono" style={{ fontSize: 11.5, color: "var(--slate)" }}>execution flow</span>
        </div>
        <div style={{ padding: 24, display: "flex", flexDirection: "column", gap: 14 }}>
          {[
            { from: "Agent", to: "Harnex MCP", label: "execute(op, params)" },
            { from: "Harnex MCP", to: "Vault", label: "fetch credentials (scoped)" },
            { from: "Vault", to: "Harnex MCP", label: "ephemeral token", muted: true },
            { from: "Harnex MCP", to: "Upstream API", label: "HTTPS request + token" },
            { from: "Upstream API", to: "Agent", label: "structured response", success: true },
          ].map((s, i) => (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <span className="mono" style={{ fontSize: 11, color: "var(--muted)", width: 28 }}>{String(i+1).padStart(2,"0")}</span>
              <span style={{ fontSize: 12.5, fontWeight: 500, width: 110 }}>{s.from}</span>
              <span style={{ color: s.muted ? "var(--muted)" : s.success ? "var(--green)" : "var(--accent)" }}>{Ic.arrow}</span>
              <span style={{ fontSize: 12.5, fontWeight: 500, width: 110 }}>{s.to}</span>
              <span className="mono" style={{ fontSize: 11.5, color: "var(--slate)", marginLeft: 8 }}>{s.label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  </section>
);

const MktPricing = ({ onEnterConsole }) => {
  const tiers = [
    { name: "Hobby", price: "Free", desc: "For solo builders and prototypes.", items: ["1 organization","3 connections","10K executions/mo","Community support"], cta: "Start free" },
    { name: "Team", price: "$99", per: "/mo", desc: "For startups shipping agents in production.", items: ["10 organizations","Unlimited connections","250K executions/mo","Email + Slack support","Audit logs"], cta: "Start trial", featured: true },
    { name: "Enterprise", price: "Custom", desc: "For platforms with multi-tenant agent products.", items: ["Unlimited orgs","Self-hosted vault","SSO + SCIM","Dedicated infra","SOC 2 + HIPAA"], cta: "Talk to sales" },
  ];
  return (
    <section id="pricing" style={{ maxWidth: 1200, margin: "0 auto", padding: "100px 32px" }}>
      <div style={{ marginBottom: 48 }}>
        <span className="kicker">Pricing</span>
        <h2 className="h-display" style={{ fontSize: 48, margin: "12px 0 0", maxWidth: 720, fontWeight: 500 }}>
          Pay for <span className="serif-i">execution</span>, not for shelf-ware.
        </h2>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16 }}>
        {tiers.map(t => (
          <div key={t.name} className="card" style={{ padding: 28, display: "flex", flexDirection: "column", gap: 18, position: "relative", borderColor: t.featured ? "var(--ink)" : "var(--border)", boxShadow: t.featured ? "var(--shadow-lg)" : "none" }}>
            {t.featured && <span style={{ position: "absolute", top: -10, right: 20, background: "var(--accent)", color: "#fff", fontSize: 10.5, fontWeight: 600, padding: "3px 8px", borderRadius: 4, textTransform: "uppercase", letterSpacing: "0.05em" }}>Recommended</span>}
            <div>
              <h3 style={{ fontSize: 14, fontWeight: 500, margin: 0, color: "var(--slate)" }}>{t.name}</h3>
              <div style={{ display: "flex", alignItems: "baseline", gap: 4, marginTop: 8 }}>
                <span className="h-display" style={{ fontSize: 40, fontWeight: 500 }}>{t.price}</span>
                {t.per && <span style={{ fontSize: 13, color: "var(--muted)" }}>{t.per}</span>}
              </div>
              <p style={{ fontSize: 13, color: "var(--muted)", margin: "8px 0 0" }}>{t.desc}</p>
            </div>
            <div className="divider"/>
            <div style={{ display: "flex", flexDirection: "column", gap: 8, flex: 1 }}>
              {t.items.map(i => (
                <div key={i} style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, color: "var(--slate)" }}>
                  <span style={{ color: "var(--accent)" }}>{Ic.check}</span>{i}
                </div>
              ))}
            </div>
            <button className={`btn ${t.featured ? "btn-accent" : "btn-secondary"} btn-lg`} onClick={onEnterConsole}>{t.cta}</button>
          </div>
        ))}
      </div>
    </section>
  );
};

const MktFooter = () => (
  <footer style={{ borderTop: "1px solid var(--border)", padding: "40px 32px", marginTop: 40 }}>
    <div style={{ maxWidth: 1200, margin: "0 auto", display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 16 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
        <HarnexLogo size={20}/>
        <span style={{ fontSize: 12, color: "var(--muted)" }}>© 2026 Harnex Labs</span>
      </div>
      <div style={{ display: "flex", gap: 20, fontSize: 12.5, color: "var(--slate)" }}>
        <a href="#docs">Docs</a>
        <a href="#changelog">Changelog</a>
        <a href="#status">Status</a>
        <a href="#privacy">Privacy</a>
        <a href="#terms">Terms</a>
      </div>
    </div>
  </footer>
);

window.Marketing = Marketing;
