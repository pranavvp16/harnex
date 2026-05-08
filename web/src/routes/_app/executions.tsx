import { useQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { useMemo, useState } from "react";

import { Ic } from "@/components/icons";
import { MethodBadge } from "@/components/ui/MethodBadge";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { useApi } from "@/lib/useApi";

export const Route = createFileRoute("/_app/executions")({
  component: ExecutionsPage,
});

function ExecutionsPage() {
  const api = useApi();
  const [statusF, setStatusF] = useState("all");
  const [search, setSearch] = useState("");

  const executions = useQuery({
    queryKey: ["executions", { limit: 200 }],
    queryFn: () => api.listExecutions({ limit: 200 }),
  });

  const filtered = useMemo(() => {
    let all = executions.data?.items ?? [];
    if (statusF !== "all") all = all.filter((e) => e.status === statusF);
    if (search) {
      const q = search.toLowerCase();
      all = all.filter(
        (e) =>
          e.path?.toLowerCase().includes(q) ||
          e.operation_id?.toLowerCase().includes(q) ||
          e.error_message?.toLowerCase().includes(q),
      );
    }
    return all;
  }, [executions.data, statusF, search]);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <div style={{ position: "relative", width: 320 }}>
          <span style={{ position: "absolute", left: 10, top: 9, color: "var(--muted)" }}>
            {Ic.search}
          </span>
          <input
            className="input"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Filter by operation path"
            style={{ paddingLeft: 30 }}
          />
        </div>
        <select
          className="select"
          style={{ width: 140 }}
          value={statusF}
          onChange={(e) => setStatusF(e.target.value)}
        >
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
        <span style={{ flex: 1 }} />
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
              <th style={{ width: 30 }} />
            </tr>
          </thead>
          <tbody>
            {filtered.map((e) => (
              <tr key={e.id} className="row-hover">
                <td className="mono" style={{ fontSize: 11.5, color: "var(--muted)" }}>
                  {new Date(e.created_at).toLocaleString()}
                </td>
                <td>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    {e.method && <MethodBadge method={e.method} />}
                    <span className="mono" style={{ fontSize: 12 }}>
                      {e.path ?? e.operation_id ?? "—"}
                    </span>
                    <span
                      style={{
                        display: "inline-flex",
                        alignItems: "center",
                        gap: 4,
                        marginLeft: 6,
                        fontSize: 11,
                        color: "var(--muted)",
                      }}
                    >
                      {e.connection_id ?? "generic"}
                    </span>
                  </div>
                  {e.error_message && (
                    <div className="mono" style={{ fontSize: 11, color: "var(--red)", marginTop: 2 }}>
                      {e.error_message}
                    </div>
                  )}
                </td>
                <td>
                  <span className="badge badge-slate">{e.mode}</span>
                </td>
                <td>
                  <StatusBadge status={e.status} />
                </td>
                <td className="mono" style={{ fontSize: 11.5, color: "var(--muted)", textAlign: "right" }}>
                  {e.duration_ms != null ? `${e.duration_ms}ms` : "—"}
                </td>
                <td>
                  <button className="btn btn-ghost btn-sm" style={{ width: 24, padding: 0 }}>
                    {Ic.chevR}
                  </button>
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={6} style={{ textAlign: "center", color: "var(--muted)", padding: 24 }}>
                  No executions yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
