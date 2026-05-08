import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useRef, useState } from "react";

import { Ic } from "@/components/icons";
import { AlertBox } from "@/components/ui/AlertBox";
import { Modal } from "@/components/ui/Modal";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { useApi } from "@/lib/useApi";

export const Route = createFileRoute("/_app/connections/$id")({
  component: ConnectionDetail,
});

const POLL_INTERVAL_MS = 3000;
const TYPICAL_INDEX_SECONDS = 60;

function ConnectionDetail() {
  const { id } = Route.useParams();
  const navigate = useNavigate();
  const api = useApi();
  const qc = useQueryClient();
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [reindexNote, setReindexNote] = useState<string | null>(null);

  const connection = useQuery({
    queryKey: ["connection", id],
    queryFn: () => api.getConnection(id),
    refetchInterval: (query) => {
      const data = query.state.data;
      if (!data) return false;
      return data.status === "pending" || data.status === "indexing" ? POLL_INTERVAL_MS : false;
    },
  });

  const indexingStartRef = useRef<number | null>(null);
  const [indexingElapsed, setIndexingElapsed] = useState(0);
  const isIndexing =
    connection.data?.status === "pending" || connection.data?.status === "indexing";
  useEffect(() => {
    if (!isIndexing) {
      indexingStartRef.current = null;
      setIndexingElapsed(0);
      return;
    }
    if (indexingStartRef.current === null) {
      indexingStartRef.current = Date.now();
    }
    const t = setInterval(() => {
      if (indexingStartRef.current !== null) {
        setIndexingElapsed(Math.floor((Date.now() - indexingStartRef.current) / 1000));
      }
    }, 1000);
    return () => clearInterval(t);
  }, [isIndexing]);

  const reindex = useMutation({
    mutationFn: () => api.reindexConnection(id),
    onSuccess: (result) => {
      setReindexNote(`Reindexed: ${result.operation_count} operations, ${result.chunk_count} chunks.`);
      void qc.invalidateQueries({ queryKey: ["connection", id] });
      void qc.invalidateQueries({ queryKey: ["connections"] });
    },
  });

  const remove = useMutation({
    mutationFn: () => api.deleteConnection(id),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["connections"] });
      void navigate({ to: "/connections" });
    },
  });

  if (connection.isLoading) {
    return <div style={{ fontSize: 13, color: "var(--muted)" }}>Loading…</div>;
  }
  if (connection.error || !connection.data) {
    return (
      <div className="card" style={{ padding: 16 }}>
        <p style={{ fontSize: 13, color: "var(--red)", marginBottom: 12 }}>
          {connection.error ? String(connection.error) : "Connection not found."}
        </p>
        <Link to="/connections">
          <button className="btn btn-ghost btn-sm">{Ic.back} Back to connections</button>
        </Link>
      </div>
    );
  }

  const c = connection.data;
  const polling = c.status === "pending" || c.status === "indexing";
  const progressPct = polling
    ? Math.min(95, Math.round((indexingElapsed / TYPICAL_INDEX_SECONDS) * 100))
    : 0;
  const phaseLabel =
    c.status === "pending"
      ? "Queued · waiting for indexer"
      : c.status === "indexing"
        ? c.endpoint_count > 0
          ? `Indexing operations · ${c.endpoint_count} so far`
          : "Fetching and parsing spec"
        : "";

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
      {/* Breadcrumb */}
      <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, marginBottom: 4 }}>
        <button className="btn btn-ghost btn-sm" onClick={() => void navigate({ to: "/connections" })}>
          {Ic.back} Back
        </button>
        <span style={{ color: "var(--muted)" }}>Connections</span>
        <span style={{ color: "var(--muted)" }}>/</span>
        <span className="mono">{c.name}</span>
      </div>

      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <div
          style={{
            width: 44,
            height: 44,
            borderRadius: 8,
            background: "var(--surface)",
            border: "1px solid var(--border)",
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            color: "var(--ink)",
            fontSize: 18,
            fontWeight: 600,
          }}
        >
          {c.name.slice(0, 1).toUpperCase()}
        </div>
        <div>
          <h2
            style={{
              fontSize: 20,
              fontWeight: 500,
              margin: 0,
              letterSpacing: "-0.01em",
            }}
            className="mono"
          >
            {c.name}
          </h2>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 4 }}>
            <StatusBadge status={c.status} />
            <span style={{ fontSize: 12, color: "var(--muted)" }}>
              {c.connector_key ?? "generic"} · {c.endpoint_count} operations indexed
            </span>
          </div>
        </div>
        <span style={{ flex: 1 }} />
        <button
          className="btn btn-secondary btn-sm"
          onClick={() => reindex.mutate()}
          disabled={reindex.isPending || c.status === "indexing"}
        >
          {Ic.refresh} Reindex
        </button>
        <button className="btn btn-ghost btn-sm">{Ic.eye} View ops</button>
        <button className="btn btn-danger btn-sm" onClick={() => setConfirmDelete(true)}>
          {Ic.trash} Delete
        </button>
      </div>

      {/* Alerts */}
      {polling && (
        <div
          className="alert alert-amber"
          style={{ display: "flex", flexDirection: "column", gap: 10, alignItems: "stretch" }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <span style={{ display: "inline-flex" }}>{Ic.refresh}</span>
            <div style={{ display: "flex", flexDirection: "column", flex: 1 }}>
              <strong>Indexing in progress</strong>
              <span style={{ fontSize: 12, color: "var(--amber-ink)" }}>
                {phaseLabel}
              </span>
            </div>
            <span className="mono" style={{ fontSize: 12, color: "var(--amber-ink)" }}>
              {indexingElapsed}s elapsed · ~{TYPICAL_INDEX_SECONDS}s typical
            </span>
          </div>
          <div
            aria-hidden
            style={{
              height: 4,
              background: "rgba(217,119,6,0.15)",
              borderRadius: 999,
              overflow: "hidden",
            }}
          >
            <div
              style={{
                width: `${progressPct}%`,
                height: "100%",
                background: "var(--amber)",
                transition: "width 0.5s ease-out",
              }}
            />
          </div>
          <div
            style={{
              display: "flex",
              gap: 16,
              fontSize: 11.5,
              color: "var(--amber-ink)",
            }}
          >
            <span>
              Operations indexed:{" "}
              <span className="mono">{c.endpoint_count}</span>
            </span>
            <span>
              Refreshing every {Math.round(POLL_INTERVAL_MS / 1000)}s
            </span>
          </div>
        </div>
      )}
      {reindexNote && (
        <AlertBox variant="info">
          <span style={{ flex: 1 }}>{reindexNote}</span>
          <button
            className="btn btn-ghost btn-sm"
            style={{ marginLeft: "auto" }}
            onClick={() => setReindexNote(null)}
          >
            Dismiss
          </button>
        </AlertBox>
      )}
      {c.last_error && c.status === "error" && (
        <div className="alert alert-red">
          <span style={{ display: "inline-flex" }}>{Ic.warning}</span>
          <div>
            <strong>Indexing failed.</strong>
            <div className="mono" style={{ fontSize: 12, marginTop: 3 }}>
              {c.last_error}
            </div>
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
            <KeyVal k="Connector" v={c.connector_key ?? "generic"} />
            <KeyVal k="Mode" v={<span className="badge badge-slate">{c.mode}</span>} />
            <KeyVal k="Auth flow" v={c.auth_flow} />
            <KeyVal k="Endpoints indexed" v={<span className="mono">{c.endpoint_count}</span>} />
            <KeyVal k="Base URL" v={<span className="mono" style={{ fontSize: 12 }}>{c.base_url ?? "—"}</span>} />
            <KeyVal k="Spec URL" v={<span className="mono" style={{ fontSize: 12 }}>{c.spec_url ?? "—"}</span>} />
            <KeyVal
              k="Last indexed"
              v={
                <span className="mono" style={{ fontSize: 12 }}>
                  {c.last_indexed_at ? new Date(c.last_indexed_at).toLocaleString() : "—"}
                </span>
              }
            />
            <KeyVal
              k="Created"
              v={<span className="mono" style={{ fontSize: 12 }}>{new Date(c.created_at).toLocaleString()}</span>}
              last
            />
          </div>
        </div>

        {/* Auth + Identifiers */}
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <div className="card">
            <div
              style={{
                padding: "12px 16px",
                borderBottom: "1px solid var(--border)",
                display: "flex",
                alignItems: "center",
                gap: 6,
              }}
            >
              <h3 style={{ fontSize: 13, fontWeight: 500, margin: 0 }}>Auth configuration</h3>
              <span className="badge badge-slate" style={{ height: 18, fontSize: 10 }}>
                {Ic.lock} public shape only
              </span>
            </div>
            <div style={{ padding: 16 }}>
              <KeyVal k="Method" v={c.auth_flow} />
              <KeyVal k="Header name" v={<span className="mono" style={{ fontSize: 12 }}>Authorization</span>} />
              <KeyVal k="Token prefix" v={<span className="mono" style={{ fontSize: 12 }}>Bearer ••••</span>} />
              <KeyVal
                k="Stored in"
                v={
                  <span
                    style={{
                      display: "inline-flex",
                      alignItems: "center",
                      gap: 4,
                      color: "var(--accent-ink)",
                    }}
                  >
                    {Ic.lock} vault
                  </span>
                }
                last
              />
            </div>
          </div>

          <div className="card">
            <div style={{ padding: "12px 16px", borderBottom: "1px solid var(--border)" }}>
              <h3 style={{ fontSize: 13, fontWeight: 500, margin: 0 }}>Identifiers</h3>
            </div>
            <div style={{ padding: 16 }}>
              <KeyVal k="Connection ID" v={<span className="mono" style={{ fontSize: 12 }}>{c.id}</span>} />
              <KeyVal k="Tenant ID" v={<span className="mono" style={{ fontSize: 12 }}>{c.tenant_id}</span>} last />
            </div>
          </div>
        </div>
      </div>

      <Modal
        open={confirmDelete}
        title="Delete connection?"
        confirmLabel="Delete"
        confirmVariant="danger"
        onConfirm={() => remove.mutate()}
        onCancel={() => setConfirmDelete(false)}
        pending={remove.isPending}
      >
        <p>
          This permanently removes <strong style={{ color: "var(--ink)" }}>{c.name}</strong> and its
          indexed operations.
        </p>
        <p style={{ color: "var(--muted)", marginTop: 8 }}>This cannot be undone.</p>
      </Modal>
    </div>
  );
}

function KeyVal({ k, v, last }: { k: string; v: React.ReactNode; last?: boolean }) {
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "140px 1fr",
        padding: "8px 0",
        borderBottom: last ? "none" : "1px solid var(--border-soft)",
        alignItems: "center",
      }}
    >
      <span style={{ fontSize: 12, color: "var(--muted)" }}>{k}</span>
      <span style={{ fontSize: 12.5 }}>{v}</span>
    </div>
  );
}
