import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, createFileRoute } from "@tanstack/react-router";
import { useMemo, useState } from "react";

import { Ic } from "@/components/icons";
import { Modal } from "@/components/ui/Modal";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { useApi } from "@/lib/useApi";
import type { Connection, ConnectionStatus } from "@/lib/api";

interface ConnectionsSearch {
  highlight?: string;
  q?: string;
  status?: string;
}

export const Route = createFileRoute("/_app/connections/")({
  validateSearch: (search: Record<string, unknown>): ConnectionsSearch => ({
    highlight: typeof search.highlight === "string" ? search.highlight : undefined,
    q: typeof search.q === "string" ? search.q : undefined,
    status: typeof search.status === "string" ? search.status : undefined,
  }),
  component: ConnectionsIndex,
});

function ConnectionsIndex() {
  const { highlight, q: initialQuery, status: statusFilter } = Route.useSearch();
  const navigate = Route.useNavigate();
  const api = useApi();
  const qc = useQueryClient();
  const [filter, setFilter] = useState(initialQuery ?? "");
  const [pendingId, setPendingId] = useState<string | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<Connection | null>(null);

  const connections = useQuery({
    queryKey: ["connections"],
    queryFn: () => api.listConnections(),
    refetchInterval: (query) => {
      const data = query.state.data as Connection[] | undefined;
      if (!data) return false;
      return data.some((c) => c.status === "pending" || c.status === "indexing") ? 3000 : false;
    },
  });

  const reindex = useMutation({
    mutationFn: async (id: string) => {
      setPendingId(id);
      try {
        return await api.reindexConnection(id);
      } finally {
        setPendingId(null);
      }
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["connections"] }),
  });

  const remove = useMutation({
    mutationFn: (id: string) => api.deleteConnection(id),
    onSuccess: () => {
      setConfirmDelete(null);
      void qc.invalidateQueries({ queryKey: ["connections"] });
    },
  });

  const counts = useMemo(() => {
    const all = connections.data ?? [];
    const byStatus: Record<ConnectionStatus, number> = {
      pending: 0,
      indexing: 0,
      ready: 0,
      error: 0,
      disabled: 0,
    };
    for (const c of all) byStatus[c.status] += 1;
    return byStatus;
  }, [connections.data]);

  const filtered = useMemo(() => {
    let all = connections.data ?? [];
    const q = filter.trim().toLowerCase();
    if (statusFilter && statusFilter !== "all") {
      all = all.filter((c) => c.status === statusFilter);
    }
    if (q) {
      all = all.filter((c) =>
        [c.name, c.connector_key, c.base_url, c.spec_url, c.auth_flow]
          .filter(Boolean)
          .some((f) => String(f).toLowerCase().includes(q)),
      );
    }
    return all;
  }, [connections.data, filter, statusFilter]);

  const data = connections.data ?? [];

  const statusCards = [
    { k: "ready", label: "Ready", color: "green" as const },
    { k: "indexing", label: "Indexing", color: "amber" as const },
    { k: "error", label: "Errored", color: "red" as const },
    { k: "disabled", label: "Disabled", color: "slate" as const },
  ];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
      {/* Status cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 10 }}>
        {statusCards.map((s) => (
          <button
            key={s.k}
            onClick={() =>
              void navigate({
                to: "/connections",
                search: (p) => ({
                  ...p,
                  status: statusFilter === s.k ? "all" : s.k,
                }),
              })
            }
            style={{
              textAlign: "left",
              padding: 12,
              background: "var(--surface)",
              border: `1px solid ${statusFilter === s.k ? "var(--ink)" : "var(--border)"}`,
              borderRadius: 8,
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: 10,
            }}
          >
            <span
              style={{
                width: 8,
                height: 8,
                borderRadius: 999,
                background:
                  s.color === "slate" ? "var(--muted)" : `var(--${s.color})`,
              }}
            />
            <span style={{ fontSize: 12, color: "var(--slate)" }}>{s.label}</span>
            <span className="h-display" style={{ marginLeft: "auto", fontSize: 22, fontWeight: 500 }}>
              {counts[s.k as ConnectionStatus]}
            </span>
          </button>
        ))}
      </div>

      {/* Toolbar */}
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <div style={{ position: "relative", width: 280 }}>
          <span style={{ position: "absolute", left: 10, top: 9, color: "var(--muted)" }}>
            {Ic.search}
          </span>
          <input
            className="input"
            value={filter}
            onChange={(e) => {
              setFilter(e.target.value);
              void navigate({
                to: "/connections",
                search: (p) => ({ ...p, q: e.target.value || undefined }),
                replace: true,
              });
            }}
            placeholder="Filter connections"
            style={{ paddingLeft: 30 }}
          />
        </div>
        <select
          className="select"
          style={{ width: 140 }}
          value={statusFilter ?? "all"}
          onChange={(e) =>
            void navigate({
              to: "/connections",
              search: (p) => ({
                ...p,
                status: e.target.value === "all" ? undefined : e.target.value,
              }),
            })
          }
        >
          <option value="all">All statuses</option>
          <option value="ready">Ready</option>
          <option value="indexing">Indexing</option>
          <option value="error">Errored</option>
          <option value="disabled">Disabled</option>
        </select>
        <button className="btn btn-ghost btn-sm">{Ic.filter} Filters</button>
        <span style={{ marginLeft: "auto" }} />
        <Link to="/connections/new">
          <button className="btn btn-primary btn-sm">{Ic.plus} New connection</button>
        </Link>
      </div>

      {connections.isLoading && (
        <div style={{ fontSize: 13, color: "var(--muted)", padding: "12px 0" }}>Loading…</div>
      )}

      {/* Empty state */}
      {!connections.isLoading && data.length === 0 && (
        <div
          className="card"
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: 12,
            padding: "48px 24px",
            textAlign: "center",
          }}
        >
          <div style={{ fontSize: 13, color: "var(--muted)" }}>No connections yet.</div>
          <Link to="/connections/new">
            <button className="btn btn-primary">{Ic.plus} Connect your first API</button>
          </Link>
        </div>
      )}

      {/* Table */}
      {data.length > 0 && (
        <div className="card" style={{ overflow: "hidden" }}>
          <table className="tbl">
            <thead>
              <tr>
                <th style={{ width: 24 }}>
                  <input type="checkbox" style={{ accentColor: "var(--ink)" }} />
                </th>
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
              {filtered.map((c) => {
                const isHighlight = c.id === highlight;
                return (
                  <tr
                    key={c.id}
                    className="row-hover"
                    style={isHighlight ? { background: "var(--accent-soft)", cursor: "pointer" } : { cursor: "pointer" }}
                    onClick={() =>
                      void navigate({ to: "/connections/$id", params: { id: c.id } })
                    }
                  >
                    <td onClick={(e) => e.stopPropagation()}>
                      <input type="checkbox" style={{ accentColor: "var(--ink)" }} />
                    </td>
                    <td>
                      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                        <span
                          style={{
                            width: 16,
                            height: 16,
                            borderRadius: 4,
                            background: "var(--bg-alt)",
                            border: "1px solid var(--border)",
                            display: "inline-flex",
                            alignItems: "center",
                            justifyContent: "center",
                            color: "var(--ink)",
                            fontSize: 10,
                            fontWeight: 600,
                          }}
                        >
                          {c.name.slice(0, 1).toUpperCase()}
                        </span>
                        <span className="mono" style={{ fontSize: 12.5, fontWeight: 500 }}>
                          {c.name}
                        </span>
                      </div>
                    </td>
                    <td>
                      <span style={{ fontSize: 12.5, color: "var(--slate)" }}>
                        {c.connector_key ?? "generic"}
                      </span>
                    </td>
                    <td>
                      <span className="badge badge-slate">{c.mode}</span>
                    </td>
                    <td>
                      <span style={{ fontSize: 12, color: "var(--slate)" }}>{c.auth_flow}</span>
                    </td>
                    <td className="mono" style={{ fontSize: 12, textAlign: "right", color: "var(--slate)" }}>
                      {c.endpoint_count}
                    </td>
                    <td>
                      <StatusBadge status={c.status} />
                    </td>
                    <td>
                      <div
                        style={{ display: "flex", gap: 4 }}
                        onClick={(e) => e.stopPropagation()}
                      >
                        <button
                          className="btn btn-ghost btn-sm"
                          title="Reindex"
                          onClick={() => reindex.mutate(c.id)}
                          disabled={pendingId === c.id || c.status === "indexing"}
                        >
                          {Ic.refresh}
                        </button>
                        <button className="btn btn-ghost btn-sm" title="More">
                          {Ic.more}
                        </button>
                        <button
                          className="btn btn-ghost btn-sm"
                          title="Delete"
                          style={{ color: "var(--red)" }}
                          onClick={() => setConfirmDelete(c)}
                        >
                          {Ic.trash}
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
              {filtered.length === 0 && (
                <tr>
                  <td
                    colSpan={8}
                    style={{ textAlign: "center", color: "var(--muted)", padding: "24px 12px" }}
                  >
                    No connections match your filter.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      <Modal
        open={!!confirmDelete}
        title="Delete connection?"
        confirmLabel="Delete"
        confirmVariant="danger"
        onConfirm={() => confirmDelete && remove.mutate(confirmDelete.id)}
        onCancel={() => setConfirmDelete(null)}
        pending={remove.isPending}
      >
        <p>
          This permanently removes{" "}
          <strong style={{ color: "var(--ink)" }}>{confirmDelete?.name}</strong> and its indexed
          operations. Stored credentials in the vault will also be deleted.
        </p>
        <p style={{ color: "var(--muted)", marginTop: 8 }}>This cannot be undone.</p>
      </Modal>
    </div>
  );
}
