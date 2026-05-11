import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useMemo, useRef, useState } from "react";

import { Ic } from "@/components/icons";
import { AlertBox } from "@/components/ui/AlertBox";
import { Field } from "@/components/ui/Field";
import { Modal } from "@/components/ui/Modal";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { useApi } from "@/lib/useApi";
import type {
  ApiKeyScope,
  ApiKeyScopeType,
  Connection,
  IssueApiKeyInput,
  IssuedApiKey,
} from "@/lib/api";

export const Route = createFileRoute("/_app/api-keys")({
  component: ApiKeysPage,
});

type ExpiresOption = "never" | "30" | "90" | "365";

const EXPIRES_LABELS: Record<ExpiresOption, string> = {
  never: "Never",
  "30": "30 days",
  "90": "90 days",
  "365": "1 year",
};

function expiresToDays(opt: ExpiresOption): number | null {
  if (opt === "never") return null;
  return Number(opt);
}

function formatExpiry(iso: string | null): string {
  if (!iso) return "Never";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "—";
  return d.toLocaleDateString();
}

function ApiKeysPage() {
  const api = useApi();
  const qc = useQueryClient();
  const [showNew, setShowNew] = useState(false);
  const [created, setCreated] = useState(false);
  const [name, setName] = useState("");
  const [scopeType, setScopeType] = useState<ApiKeyScopeType>("all");
  const [scopeIds, setScopeIds] = useState<string[]>([]);
  const [expires, setExpires] = useState<ExpiresOption>("never");
  const [copied, setCopied] = useState(false);
  const [issued, setIssued] = useState<IssuedApiKey | null>(null);
  const [confirmRevoke, setConfirmRevoke] = useState<{ id: string; name: string } | null>(null);
  const copyRevealRef = useRef<HTMLButtonElement>(null);

  const keys = useQuery({ queryKey: ["api-keys"], queryFn: () => api.listApiKeys() });
  const connections = useQuery({
    queryKey: ["connections"],
    queryFn: () => api.listConnections(),
    enabled: showNew,
  });

  const issue = useMutation({
    mutationFn: (input: IssueApiKeyInput) => api.issueApiKey(input),
    onSuccess: (key) => {
      setIssued(key);
      setCreated(true);
      void qc.invalidateQueries({ queryKey: ["api-keys"] });
    },
  });

  const revoke = useMutation({
    mutationFn: (id: string) => api.revokeApiKey(id),
    onSuccess: () => {
      setConfirmRevoke(null);
      void qc.invalidateQueries({ queryKey: ["api-keys"] });
    },
  });

  useEffect(() => {
    if (created && issued) {
      copyRevealRef.current?.focus();
    }
  }, [created, issued]);

  function handleIssue() {
    const scope: ApiKeyScope =
      scopeType === "all"
        ? { type: "all", connection_ids: [] }
        : { type: "connections", connection_ids: scopeIds };
    issue.mutate({
      name: name.trim(),
      scope,
      expires_in_days: expiresToDays(expires),
    });
  }

  const copyToken = () => {
    if (!issued) return;
    void navigator.clipboard.writeText(issued.plaintext);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const closeNew = () => {
    setShowNew(false);
    setCreated(false);
    setIssued(null);
    setName("");
    setScopeType("all");
    setScopeIds([]);
    setExpires("never");
  };

  const submitDisabled =
    !name.trim() ||
    issue.isPending ||
    (scopeType === "connections" && scopeIds.length === 0);

  const scopeError =
    scopeType === "connections" && scopeIds.length === 0
      ? "Select at least one connection or switch to All connections."
      : undefined;

  const connectionsById = useMemo(() => {
    const map = new Map<string, Connection>();
    for (const c of connections.data ?? []) map.set(c.id, c);
    return map;
  }, [connections.data]);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
      {!showNew ? (
        <>
          <div className="responsive-toolbar" style={{ alignItems: "flex-start" }}>
            <div className="toolbar-search">
              <h2 className="h-display" style={{ fontSize: 20, margin: 0, fontWeight: 500 }}>
                API <span className="serif-i">keys</span>
              </h2>
              <p style={{ fontSize: 12.5, color: "var(--muted)", margin: "4px 0 0" }}>
                Keys authenticate your agents and runtime against the Harnex MCP server.
              </p>
            </div>
            <span className="toolbar-spacer" />
            <button
              className="btn btn-primary btn-sm"
              onClick={() => {
                setShowNew(true);
                setCreated(false);
              }}
            >
              {Ic.plus} Issue new key
            </button>
          </div>

          <div className="card table-scroll">
            <table className="tbl">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Prefix</th>
                  <th>Scope</th>
                  <th>Expires</th>
                  <th>Last used</th>
                  <th>Created</th>
                  <th style={{ width: 100, textAlign: "right" }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {keys.data?.map((k) => (
                  <tr key={k.id} className="row-hover">
                    <td>
                      <span style={{ fontWeight: 500, fontSize: 13 }}>{k.name}</span>
                    </td>
                    <td>
                      <span className="mono" style={{ fontSize: 12 }}>
                        {k.key_prefix}_••••••••
                      </span>
                    </td>
                    <td>
                      {k.scope.type === "all" ? (
                        <span className="badge badge-slate">All connections</span>
                      ) : (
                        <span className="badge badge-accent">
                          {k.scope.connection_ids.length} connection
                          {k.scope.connection_ids.length === 1 ? "" : "s"}
                        </span>
                      )}
                    </td>
                    <td>
                      <span style={{ fontSize: 12, color: "var(--slate)" }}>
                        {formatExpiry(k.expires_at)}
                      </span>
                    </td>
                    <td>
                      <span className="mono" style={{ fontSize: 11.5, color: "var(--muted)" }}>
                        {k.last_used_at ? new Date(k.last_used_at).toLocaleString() : "never"}
                      </span>
                    </td>
                    <td>
                      <span className="mono" style={{ fontSize: 11.5, color: "var(--muted)" }}>
                        {new Date(k.created_at).toLocaleString()}
                      </span>
                    </td>
                    <td style={{ textAlign: "right" }}>
                      <button
                        className="btn btn-danger btn-sm"
                        onClick={() => setConfirmRevoke({ id: k.id, name: k.name })}
                        disabled={revoke.isPending}
                      >
                        Revoke
                      </button>
                    </td>
                  </tr>
                ))}
                {(!keys.data || keys.data.length === 0) && (
                  <tr>
                    <td colSpan={7} style={{ textAlign: "center", color: "var(--muted)", padding: 24 }}>
                      No keys yet.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </>
      ) : (
        <div className="card" style={{ padding: 20, maxWidth: 640, width: "100%" }}>
          <div className="responsive-toolbar" style={{ alignItems: "center", marginBottom: 14 }}>
            <h2 className="h-display" style={{ fontSize: 20, margin: 0, fontWeight: 500 }}>
              Issue new key
            </h2>
            <span className="toolbar-spacer" />
            <button className="btn btn-ghost btn-sm" onClick={closeNew} aria-label="Close">
              {Ic.x}
            </button>
          </div>

          {!created ? (
            <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
              <Field label="Key name" htmlFor="key-name" hint="Used in audit logs and the keys list.">
                <Input
                  id="key-name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="production-agent"
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !submitDisabled) handleIssue();
                  }}
                />
              </Field>

              <Field
                label="Scope"
                htmlFor="key-scope"
                hint="Restrict which connections this key may execute against."
              >
                <Select
                  id="key-scope"
                  value={scopeType}
                  onChange={(e) => setScopeType(e.target.value as ApiKeyScopeType)}
                >
                  <option value="all">All connections</option>
                  <option value="connections">Specific connections…</option>
                </Select>
              </Field>

              {scopeType === "connections" && (
                <Field
                  label="Connections"
                  htmlFor="key-conn-list"
                  hint={
                    connections.isLoading
                      ? "Loading connections…"
                      : "Hold ⌘ / Ctrl to select multiple."
                  }
                  error={scopeError}
                >
                  <select
                    id="key-conn-list"
                    multiple
                    className="select"
                    style={{ minHeight: 120, padding: "8px 10px" }}
                    value={scopeIds}
                    onChange={(e) =>
                      setScopeIds(
                        Array.from(e.target.selectedOptions, (o) => o.value),
                      )
                    }
                    disabled={connections.isLoading}
                  >
                    {(connections.data ?? []).map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.name} · {c.connector_key ?? "generic"}
                      </option>
                    ))}
                  </select>
                  {scopeIds.length > 0 && (
                    <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginTop: 6 }}>
                      {scopeIds.map((id) => (
                        <span key={id} className="badge badge-slate badge-mono">
                          {connectionsById.get(id)?.name ?? id.slice(0, 8)}
                        </span>
                      ))}
                    </div>
                  )}
                </Field>
              )}

              <Field
                label="Expires"
                htmlFor="key-expires"
                hint="Expired keys are rejected at MCP authentication time."
              >
                <Select
                  id="key-expires"
                  value={expires}
                  onChange={(e) => setExpires(e.target.value as ExpiresOption)}
                >
                  {(["never", "30", "90", "365"] as ExpiresOption[]).map((opt) => (
                    <option key={opt} value={opt}>
                      {EXPIRES_LABELS[opt]}
                    </option>
                  ))}
                </Select>
              </Field>

              {issue.error && (
                <AlertBox variant="red">
                  <span style={{ display: "inline-flex" }}>{Ic.warning}</span>
                  <div>Failed to issue key: {String(issue.error)}</div>
                </AlertBox>
              )}

              <div className="wizard-actions" style={{ marginTop: 4 }}>
                <span className="toolbar-spacer" />
                <button className="btn btn-ghost" onClick={closeNew}>
                  Cancel
                </button>
                <button
                  className="btn btn-accent"
                  onClick={handleIssue}
                  disabled={submitDisabled}
                >
                  {issue.isPending ? "Issuing…" : "Issue key"}
                </button>
              </div>
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
              <AlertBox variant="amber">
                <span style={{ display: "inline-flex" }}>{Ic.warning}</span>
                <div>
                  <strong>Save this key now.</strong> Harnex will not show it again. Treat it like a
                  password.
                </div>
              </AlertBox>
              <div
                aria-live="polite"
                aria-label="Your new API key"
                style={{
                  padding: 14,
                  borderRadius: 6,
                  display: "flex",
                  alignItems: "center",
                  flexWrap: "wrap",
                  gap: 10,
                  border: "1px solid var(--border-strong)",
                  background: "#0f0f12",
                  color: "var(--logo-ink-on-dark)",
                }}
              >
                <span className="mono" style={{ flex: 1, fontSize: 12.5, wordBreak: "break-all" }}>
                  {issued?.plaintext}
                </span>
                <button
                  ref={copyRevealRef}
                  type="button"
                  className="btn btn-ghost btn-sm"
                  style={{
                    background: "rgba(255,255,255,0.12)",
                    color: "var(--logo-ink-on-dark)",
                    borderColor: "rgba(255,255,255,0.28)",
                  }}
                  onClick={copyToken}
                >
                  {Ic.copy} {copied ? "Copied!" : "Copy"}
                </button>
              </div>
              {issued && (
                <div
                  style={{
                    fontSize: 12,
                    color: "var(--muted)",
                    display: "flex",
                    flexDirection: "column",
                    gap: 4,
                  }}
                >
                  <div>
                    <span style={{ color: "var(--slate)" }}>Scope:</span>{" "}
                    {issued.scope.type === "all"
                      ? "all connections"
                      : `${issued.scope.connection_ids.length} connection${issued.scope.connection_ids.length === 1 ? "" : "s"}`}
                  </div>
                  <div>
                    <span style={{ color: "var(--slate)" }}>Expires:</span>{" "}
                    {formatExpiry(issued.expires_at)}
                  </div>
                </div>
              )}
              <div className="wizard-actions">
                <span className="toolbar-spacer" />
                <button className="btn btn-primary" onClick={closeNew}>
                  Done
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      <Modal
        open={confirmRevoke !== null}
        title="Revoke API key?"
        confirmLabel="Revoke"
        confirmVariant="danger"
        onConfirm={() => {
          if (confirmRevoke) revoke.mutate(confirmRevoke.id);
        }}
        onCancel={() => setConfirmRevoke(null)}
        pending={revoke.isPending}
      >
        <p>
          This permanently deactivates{" "}
          <strong style={{ color: "var(--ink)" }}>{confirmRevoke?.name ?? "this key"}</strong>.
          Any agents using it will fail to authenticate.
        </p>
        <p style={{ color: "var(--muted)", marginTop: 8 }}>This cannot be undone.</p>
      </Modal>
    </div>
  );
}
