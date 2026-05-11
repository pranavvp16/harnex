import { useMutation, useQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";

import { Ic } from "@/components/icons";
import { MethodBadge } from "@/components/ui/MethodBadge";
import { useApi } from "@/lib/useApi";
import type { SearchResponse, SearchHit } from "@/lib/api";

export const Route = createFileRoute("/_app/search")({
  component: SearchPage,
});

const EXAMPLE_QUERIES = [
  "list pull requests for repo",
  "create a stripe customer",
  "post a slack message",
  "list datadog incidents in last 24h",
  "update a linear issue's status",
];

function SearchPage() {
  const api = useApi();
  const [query, setQuery] = useState("list pull requests for repo");
  const [topK, setTopK] = useState(5);
  const [connectorFilter, setConnectorFilter] = useState("");
  const [results, setResults] = useState<SearchHit[]>([]);
  const [loading, setLoading] = useState(false);
  const [showAmbig, setShowAmbig] = useState(false);

  const connectors = useQuery({
    queryKey: ["connectors"],
    queryFn: () => api.listConnectors(),
  });

  const search = useMutation<SearchResponse, Error, void>({
    mutationFn: () =>
      api.search({ query, top_k: topK, connector_filter: connectorFilter || null }),
    onSuccess: (data) => {
      setShowAmbig(data.clarification_needed);
      setResults(data.hits);
    },
  });

  const handleSearch = () => {
    if (!query.trim()) return;
    setLoading(true);
    search.mutate(undefined, {
      onSettled: () => setLoading(false),
    });
  };

  return (
    <div className="responsive-split" style={{ gap: 14, height: "100%" }}>
      <div style={{ display: "flex", flexDirection: "column", gap: 12, minHeight: 0 }}>
        <div className="card" style={{ padding: 14, display: "flex", flexDirection: "column", gap: 10 }}>
          <div style={{ position: "relative" }}>
            <span style={{ position: "absolute", left: 12, top: 11, color: "var(--muted)" }}>
              {Ic.search}
            </span>
            <input
              className="input"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              placeholder='Try: "list pull requests for repo"'
              style={{ height: 40, paddingLeft: 34, fontSize: 14 }}
            />
          </div>
          <div className="responsive-toolbar">
            <select
              className="select toolbar-control"
              style={{ width: 180 }}
              value={connectorFilter}
              onChange={(e) => setConnectorFilter(e.target.value)}
            >
              <option value="">All connectors</option>
              {connectors.data?.map((c) => (
                <option key={c.key} value={c.key}>
                  {c.display_name}
                </option>
              ))}
            </select>
            <div className="toolbar-control" style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <span style={{ fontSize: 12, color: "var(--muted)" }}>top_k</span>
              <input
                type="number"
                className="input"
                min={1}
                max={20}
                value={topK}
                onChange={(e) => setTopK(parseInt(e.target.value) || 5)}
                style={{ width: 64 }}
              />
            </div>
            <span className="toolbar-spacer" />
            <button className="btn btn-primary btn-sm" onClick={handleSearch} disabled={search.isPending}>
              {Ic.search} Search
            </button>
          </div>
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap", paddingTop: 4 }}>
            {EXAMPLE_QUERIES.map((q) => (
              <button
                key={q}
                onClick={() => {
                  setQuery(q);
                  setTimeout(handleSearch, 0);
                }}
                style={{
                  fontSize: 11.5,
                  padding: "3px 8px",
                  background: "var(--surface-2)",
                  border: "1px solid var(--border)",
                  borderRadius: 999,
                  color: "var(--slate)",
                  cursor: "pointer",
                }}
              >
                {q}
              </button>
            ))}
          </div>
        </div>

        {showAmbig && (
          <div className="alert alert-amber">
            <span style={{ display: "inline-flex" }}>{Ic.warning}</span>
            <div>
              <strong>Ambiguous query.</strong> Multiple operations matched. Consider clarifying
              which resource (e.g. &quot;update a Linear <em>issue</em> status&quot; vs.
              &quot;update a GitHub <em>PR</em>&quot;).
            </div>
          </div>
        )}

        <div
          className="card"
          style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden", minHeight: 0 }}
        >
          <div
            style={{
              padding: "10px 14px",
              borderBottom: "1px solid var(--border)",
              display: "flex",
              alignItems: "center",
            }}
          >
            <span className="kicker">Results</span>
            <span
              style={{ marginLeft: "auto", fontSize: 11, color: "var(--muted)" }}
              className="mono"
            >
              {loading ? "searching…" : `${results.length} results`}
            </span>
          </div>
          <div
            style={{ flex: 1, overflow: "auto", padding: 10, display: "flex", flexDirection: "column", gap: 8 }}
          >
            {loading && (
              <div style={{ padding: 30, textAlign: "center", color: "var(--muted)", fontSize: 12.5 }}>
                Searching across operations…
              </div>
            )}
            {!loading && results.length === 0 && (
              <div style={{ padding: 30, textAlign: "center", color: "var(--muted)" }}>
                <div style={{ marginBottom: 6 }}>{Ic.search}</div>
                <div style={{ fontSize: 13 }}>No operations matched.</div>
              </div>
            )}
            {!loading &&
              results.map((r, i) => (
                <div
                  key={`${r.connection_id}:${r.operation_id}`}
                  style={{
                    border: "1px solid var(--border)",
                    borderRadius: 6,
                    padding: "10px 12px",
                    background: i === 0 ? "var(--accent-soft)" : "var(--surface)",
                    borderColor: i === 0 ? "var(--accent-border)" : "var(--border)",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                    <MethodBadge method={r.method} />
                    <span className="mono min-w-0" style={{ fontSize: 12.5, fontWeight: 500, wordBreak: "break-word" }}>
                      {r.path}
                    </span>
                    <span style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                      <span
                        style={{
                          display: "inline-flex",
                          alignItems: "center",
                          gap: 4,
                          fontSize: 11.5,
                          color: "var(--muted)",
                        }}
                      >
                        {r.connector_key ?? "generic"}
                      </span>
                      <span
                        className="mono"
                        style={{
                          fontSize: 11,
                          padding: "2px 6px",
                          borderRadius: 3,
                          background: i === 0 ? "rgba(154,52,18,0.12)" : "var(--bg-alt)",
                          color: i === 0 ? "var(--accent-ink)" : "var(--slate)",
                          fontWeight: 500,
                        }}
                      >
                        {r.score.toFixed(2)}
                      </span>
                    </span>
                  </div>
                  <div style={{ fontSize: 12.5, color: "var(--slate)", marginTop: 4 }}>
                    {r.summary}
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 4, flexWrap: "wrap" }}>
                    <span className="mono min-w-0" style={{ fontSize: 11, color: "var(--muted)", wordBreak: "break-word" }}>
                      op: {r.operation_id}
                    </span>
                    <span style={{ marginLeft: "auto" }}>
                      <button className="btn btn-ghost btn-sm" style={{ height: 22, fontSize: 11 }}>
                        {Ic.terminal} Try execute
                      </button>
                    </span>
                  </div>
                </div>
              ))}
          </div>
        </div>
      </div>

      {/* Right: MCP request preview */}
      <div className="card" style={{ display: "flex", flexDirection: "column", overflow: "hidden", minHeight: 0 }}>
        <div
          style={{
            padding: "10px 14px",
            borderBottom: "1px solid var(--border)",
            display: "flex",
            alignItems: "center",
            gap: 6,
          }}
        >
          <span className="kicker">MCP request</span>
          <span style={{ marginLeft: "auto" }}>
            <button className="btn btn-ghost btn-sm">{Ic.copy} Copy</button>
          </span>
        </div>
        <pre
          style={{
            margin: 0,
            padding: 14,
            fontFamily: "var(--font-mono)",
            fontSize: 11.5,
            color: "var(--slate)",
            overflow: "auto",
            lineHeight: 1.5,
            flex: 1,
          }}
        >
          {`POST /mcp/v1/tools/search
Authorization: Bearer hx_live_•••••
Content-Type: application/json

{
  "query": ${JSON.stringify(query)},
  "top_k": ${topK},
  "filter": {
    "connector": ${JSON.stringify(connectorFilter || null)}
  }
}

→ 200 OK · 84ms

{
  "results": [
${results
  .slice(0, 3)
  .map(
    (r) =>
      `    {
      "method": "${r.method}",
      "path": "${r.path}",
      "summary": "${r.summary}",
      "connector": "${r.connector_key ?? "generic"}",
      "operation_id": "${r.operation_id}",
      "score": ${r.score.toFixed(2)}
    }`,
  )
  .join(",\n")}${results.length > 3 ? ",\n    ..." : ""}
  ]
}`}
        </pre>
      </div>
    </div>
  );
}
