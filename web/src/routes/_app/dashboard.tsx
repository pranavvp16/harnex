import { useQuery } from "@tanstack/react-query";
import { Link, createFileRoute } from "@tanstack/react-router";
import { Ic } from "@/components/icons";
import { KpiCard } from "@/components/ui/KpiCard";
import { MethodBadge } from "@/components/ui/MethodBadge";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { useApi } from "@/lib/useApi";
import type { Connection, ConnectionStatus } from "@/lib/api";

export const Route = createFileRoute("/_app/dashboard")({
  component: Dashboard,
});

function Dashboard() {
  const api = useApi();
  const connections = useQuery({
    queryKey: ["connections"],
    queryFn: () => api.listConnections(),
  });
  const usage = useQuery({
    queryKey: ["usage", "current"],
    queryFn: () => api.getCurrentUsage(),
  });
  const recent = useQuery({
    queryKey: ["executions", { limit: 7 }],
    queryFn: () => api.listExecutions({ limit: 7 }),
  });

  const total = connections.data?.length ?? 0;
  const counts = countByStatus(connections.data ?? []);
  const u = usage.data;

  const noConnections = !connections.isLoading && total === 0;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      {/* Banner */}
      {noConnections && (
        <div className="alert alert-accent" style={{ alignItems: "center" }}>
          <span style={{ display: "inline-flex" }}>{Ic.spark}</span>
          <div style={{ flex: 1 }}>
            <strong style={{ fontWeight: 500 }}>Connect your first API.</strong>
            <span style={{ marginLeft: 8, color: "var(--accent-ink)", opacity: 0.85 }}>
              Index any HTTP API in under a minute.
            </span>
          </div>
          <Link to="/connections/new">
            <button className="btn btn-accent btn-sm">
              {Ic.plus} Connect an API
            </button>
          </Link>
        </div>
      )}

      {/* KPIs */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12 }}>
        <KpiCard
          label="Connections"
          value={connections.isLoading ? "—" : total}
          sub={
            total > 0
              ? `${counts.ready} ready · ${counts.indexing + counts.pending} indexing · ${counts.error} error`
              : "none yet"
          }
        />
        <KpiCard
          label="Executions"
          value={u ? u.executions.toLocaleString() : "—"}
          sub="this month"
        />
        <KpiCard
          label="Searches"
          value={u ? u.searches.toLocaleString() : "—"}
          sub="this month"
        />
      </div>

      {/* Two-col */}
      <div style={{ display: "grid", gridTemplateColumns: "1.4fr 1fr", gap: 12 }}>
        {/* Recent executions */}
        <div className="card">
          <div
            style={{
              padding: "12px 16px",
              borderBottom: "1px solid var(--border)",
              display: "flex",
              alignItems: "center",
              gap: 8,
            }}
          >
            <h3 style={{ fontSize: 13, fontWeight: 500, margin: 0 }}>Recent executions</h3>
            <Link to="/executions" style={{ marginLeft: "auto" }}>
              <button className="btn btn-ghost btn-sm">
                View all {Ic.arrow}
              </button>
            </Link>
          </div>
          {recent.isLoading && (
            <div style={{ padding: 16, fontSize: 13, color: "var(--muted)" }}>Loading…</div>
          )}
          {recent.data && recent.data.items.length === 0 && (
            <div style={{ padding: 16, fontSize: 13, color: "var(--muted)" }}>
              No executions yet — use the MCP execute tool to populate this.
            </div>
          )}
          {recent.data && recent.data.items.length > 0 && (
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
                {recent.data.items.map((e) => (
                  <tr key={e.id} className="row-hover">
                    <td className="mono" style={{ fontSize: 11.5, color: "var(--muted)" }}>
                      {new Date(e.created_at).toLocaleTimeString()}
                    </td>
                    <td>
                      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                        {e.method && <MethodBadge method={e.method} />}
                        <span className="mono" style={{ fontSize: 12 }}>
                          {e.path ?? e.operation_id ?? "—"}
                        </span>
                      </div>
                    </td>
                    <td>
                      <StatusBadge status={e.status} />
                    </td>
                    <td
                      className="mono"
                      style={{ fontSize: 11.5, color: "var(--muted)", textAlign: "right" }}
                    >
                      {e.duration_ms != null ? `${e.duration_ms}ms` : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Health + quota */}
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <div className="card" style={{ padding: 16 }}>
            <div style={{ display: "flex", alignItems: "center", marginBottom: 14 }}>
              <h3 style={{ fontSize: 13, fontWeight: 500, margin: 0 }}>Connection health</h3>
              <Link to="/connections" style={{ marginLeft: "auto" }}>
                <button className="btn btn-ghost btn-sm">Manage {Ic.arrow}</button>
              </Link>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 8 }}>
              <HealthBox label="Ready" count={counts.ready} color="green" />
              <HealthBox label="Indexing" count={counts.indexing + counts.pending} color="amber" />
              <HealthBox label="Errored" count={counts.error} color="red" />
            </div>
            <div style={{ height: 16 }} />
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              {(connections.data ?? []).slice(0, 4).map((c) => (
                <div
                  key={c.id}
                  style={{ display: "flex", alignItems: "center", gap: 8, padding: "5px 0" }}
                >
                  <span
                    style={{
                      width: 6,
                      height: 6,
                      borderRadius: 999,
                      background:
                        c.status === "ready"
                          ? "var(--green)"
                          : c.status === "error"
                          ? "var(--red)"
                          : "var(--amber)",
                    }}
                  />
                  <span className="mono" style={{ fontSize: 12 }}>{c.name}</span>
                  <span style={{ marginLeft: "auto" }}>
                    <StatusBadge status={c.status} />
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div className="card" style={{ padding: 16 }}>
            <div style={{ display: "flex", alignItems: "center", marginBottom: 12 }}>
              <h3 style={{ fontSize: 13, fontWeight: 500, margin: 0 }}>Usage this month</h3>
              <span
                style={{ marginLeft: "auto", fontSize: 11.5, color: "var(--muted)" }}
                className="mono"
              >
                {u?.year_month ?? "—"}
              </span>
            </div>
            <QuotaRow
              label="Executions"
              used={u?.executions ?? 0}
              cap={u?.monthly_execution_quota ?? 0}
            />
            <UsageRow label="Searches" value={u?.searches ?? 0} />
            <UsageRow label="Embedding tokens" value={u?.embedding_tokens ?? 0} />
          </div>
        </div>
      </div>
    </div>
  );
}

function HealthBox({ label, count, color }: { label: string; count: number; color: "green" | "amber" | "red" }) {
  const map = {
    green: { bg: "var(--green-soft)", b: "var(--green-border)", c: "var(--green-ink)" },
    amber: { bg: "var(--amber-soft)", b: "var(--amber-border)", c: "var(--amber-ink)" },
    red: { bg: "var(--red-soft)", b: "var(--red-border)", c: "var(--red-ink)" },
  };
  const v = map[color];
  return (
    <div
      style={{
        background: v.bg,
        border: `1px solid ${v.b}`,
        borderRadius: 6,
        padding: "10px 12px",
      }}
    >
      <div className="h-display" style={{ fontSize: 22, color: v.c, fontWeight: 500 }}>
        {count}
      </div>
      <div style={{ fontSize: 11, color: v.c, opacity: 0.8 }}>{label}</div>
    </div>
  );
}

function QuotaRow({ label, used, cap, unit }: { label: string; used: number; cap: number; unit?: string }) {
  const hasCap = cap > 0;
  const pct = hasCap ? Math.min(100, (used / cap) * 100) : 0;
  const color = pct > 80 ? "var(--accent)" : pct > 60 ? "var(--amber)" : "var(--ink)";
  return (
    <div style={{ marginBottom: 10 }}>
      <div style={{ display: "flex", alignItems: "center", marginBottom: 4 }}>
        <span style={{ fontSize: 12 }}>{label}</span>
        <span className="mono" style={{ marginLeft: "auto", fontSize: 11, color: "var(--muted)" }}>
          {used.toLocaleString()}
          {unit ?? ""}
          {hasCap ? ` / ${cap.toLocaleString()}${unit ?? ""}` : ""}
        </span>
      </div>
      {hasCap && (
        <div style={{ height: 5, background: "var(--border)", borderRadius: 3, overflow: "hidden" }}>
          <div style={{ width: `${pct}%`, height: "100%", background: color }} />
        </div>
      )}
    </div>
  );
}

function UsageRow({ label, value, unit }: { label: string; value: number; unit?: string }) {
  return (
    <div style={{ marginBottom: 10, display: "flex", alignItems: "center" }}>
      <span style={{ fontSize: 12 }}>{label}</span>
      <span className="mono" style={{ marginLeft: "auto", fontSize: 11, color: "var(--muted)" }}>
        {value.toLocaleString()}
        {unit ?? ""}
      </span>
    </div>
  );
}

function countByStatus(rows: Connection[]): Record<ConnectionStatus, number> {
  const out: Record<ConnectionStatus, number> = {
    pending: 0,
    indexing: 0,
    ready: 0,
    error: 0,
    disabled: 0,
  };
  for (const r of rows) out[r.status] += 1;
  return out;
}
