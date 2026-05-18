import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";
import { useState } from "react";

import { Ic } from "@/components/icons";
import { AlertBox } from "@/components/ui/AlertBox";
import { BareUrlForm } from "@/components/wizard/BareUrlForm";
import { BuiltinConnectorForm } from "@/components/wizard/BuiltinConnectorForm";
import type { BuiltinConnectorKey } from "@/components/wizard/BuiltinConnectorForm";
import { OpenApiUploadForm } from "@/components/wizard/OpenApiUploadForm";
import { OpenApiUrlForm } from "@/components/wizard/OpenApiUrlForm";
import type { WizardFormState } from "@/components/wizard/types";
import type { ConnectionTestResult } from "@/lib/api";
import { useApi } from "@/lib/useApi";

export type WizardChoice =
  | { kind: "builtin"; connectorKey: BuiltinConnectorKey }
  | { kind: "openapi_url" }
  | { kind: "openapi_upload" }
  | { kind: "bare_url" };

type Step = 1 | 2 | 3;

export function ConnectionWizard() {
  const [step, setStep] = useState<Step>(1);
  const [picked, setPicked] = useState<string | null>(null);
  const [formState, setFormState] = useState<WizardFormState | null>(null);
  const [testResult, setTestResult] = useState<ConnectionTestResult | null>(null);
  const navigate = useNavigate();
  const api = useApi();
  const qc = useQueryClient();

  const create = useMutation({
    mutationFn: async (state: WizardFormState) => {
      const created = await api.createConnection(state.payload);
      if (state.file) {
        await api.uploadOpenApiSpec(created.id, state.file);
      }
      return created;
    },
    onSuccess: async (created) => {
      await qc.invalidateQueries({ queryKey: ["connections"] });
      void navigate({ to: "/connections/$id", params: { id: created.id } });
    },
  });

  const test = useMutation({
    mutationFn: async (state: WizardFormState) => {
      return api.testConnection({
        mode: state.payload.mode,
        connector_key: state.payload.connector_key ?? null,
        base_url: state.payload.base_url ?? null,
        auth_flow: state.payload.auth_flow,
        auth_config: state.payload.auth_config,
        credentials: state.payload.credentials,
      });
    },
    onSuccess: (result) => setTestResult(normalizeProbeResult(result)),
    onError: () => setTestResult(null),
  });

  const tiles = [
    {
      id: "github",
      name: "GitHub",
      desc: "Connect GitHub orgs and repos. Auth via OAuth or PAT.",
      icon: (
        <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 .3a12 12 0 0 0-3.8 23.4c.6.1.8-.3.8-.6v-2.2c-3.3.7-4-1.4-4-1.4-.6-1.4-1.4-1.8-1.4-1.8-1.1-.7.1-.7.1-.7 1.2.1 1.9 1.2 1.9 1.2 1.1 1.9 2.9 1.4 3.6 1 .1-.8.4-1.4.7-1.7-2.6-.3-5.4-1.3-5.4-5.9 0-1.3.5-2.4 1.2-3.2-.1-.3-.5-1.5.1-3.2 0 0 1-.3 3.2 1.2.9-.3 1.9-.4 2.9-.4 1 0 2 .1 2.9.4 2.2-1.5 3.2-1.2 3.2-1.2.6 1.7.2 2.9.1 3.2.7.8 1.2 1.9 1.2 3.2 0 4.6-2.8 5.6-5.5 5.9.4.4.8 1.1.8 2.2v3.3c0 .3.2.7.8.6A12 12 0 0 0 12 .3" />
        </svg>
      ),
      pick: { kind: "builtin" as const, connectorKey: "github" as const },
    },
    {
      id: "jenkins",
      name: "Jenkins",
      desc: "Build, queue, and job APIs from a Jenkins controller.",
      icon: (
        <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
          <circle cx="12" cy="10" r="4" />
          <path d="M9 14h6l1 6H8z" />
        </svg>
      ),
      pick: { kind: "builtin" as const, connectorKey: "jenkins" as const },
    },
    {
      id: "gitlab",
      name: "GitLab",
      desc: "Self-hosted or SaaS GitLab projects and pipelines.",
      icon: (
        <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 21 3 13l1.5-5h2L8.5 13h7L17.5 8h2L21 13z" />
        </svg>
      ),
      pick: { kind: "builtin" as const, connectorKey: "gitlab" as const },
    },
    {
      id: "jira",
      name: "Jira",
      desc: "Issues, sprints, and project APIs from Atlassian.",
      icon: (
        <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 4 L20 12 L16 16 L12 12 L8 16 L4 12 z" />
        </svg>
      ),
      pick: { kind: "builtin" as const, connectorKey: "jira" as const },
    },
    {
      id: "linear",
      name: "Linear",
      desc: "Issues, cycles, and team APIs from Linear.",
      icon: (
        <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
          <circle cx="12" cy="12" r="8" stroke="currentColor" strokeWidth="1.5" fill="none" />
          <path d="M6 12 L18 12 M6 8 L18 8 M6 16 L18 16" stroke="currentColor" strokeWidth="1.5" />
        </svg>
      ),
      pick: { kind: "builtin" as const, connectorKey: "linear" as const },
    },
    {
      id: "slack",
      name: "Slack",
      desc: "Messages, channels, and user APIs from Slack.",
      icon: (
        <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
          <rect x="4" y="10" width="6" height="2" rx="1" />
          <rect x="14" y="12" width="6" height="2" rx="1" />
          <rect x="10" y="4" width="2" height="6" rx="1" />
          <rect x="12" y="14" width="2" height="6" rx="1" />
        </svg>
      ),
      pick: { kind: "builtin" as const, connectorKey: "slack" as const },
    },
    {
      id: "stripe",
      name: "Stripe",
      desc: "Payments, customers, subscriptions, and billing APIs.",
      icon: (
        <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
          <path d="M13.976 9.15c-2.172-.806-3.356-1.426-3.356-2.409 0-.831.683-1.305 1.901-1.305 2.227 0 4.515.858 6.09 1.631l.89-5.494C18.252.975 15.697 0 12.165 0 9.667 0 7.589.654 6.104 1.872 4.56 3.147 3.757 4.992 3.757 7.218c0 4.039 2.467 5.76 6.476 7.219 2.585.92 3.445 1.574 3.445 2.583 0 .98-.84 1.545-2.354 1.545-1.875 0-4.965-.921-6.99-2.109l-.9 5.555C5.175 22.99 8.385 24 11.714 24c2.641 0 4.843-.624 6.328-1.813 1.664-1.305 2.525-3.236 2.525-5.732 0-4.128-2.524-5.851-6.591-7.305z" />
        </svg>
      ),
      pick: { kind: "builtin" as const, connectorKey: "stripe" as const },
    },
    {
      id: "kubernetes",
      name: "Kubernetes",
      desc: "Cluster API via bearer token or basic auth.",
      icon: (
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
          <path d="M12 4 L19 8 L17 16 L12 20 L7 16 L5 8 z" />
          <circle cx="12" cy="12" r="2" fill="currentColor" />
        </svg>
      ),
      pick: { kind: "builtin" as const, connectorKey: "kubernetes" as const },
    },
    {
      id: "openapi",
      name: "OpenAPI URL",
      desc: "Point to an OpenAPI 3.x JSON or YAML spec by URL.",
      icon: (
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="7" strokeWidth="1.5" fill="none" />
          <circle cx="12" cy="12" r="2" fill="currentColor" />
          <path d="M5 12 H8 M16 12 H19" strokeWidth="1.5" />
        </svg>
      ),
      pick: { kind: "openapi_url" as const },
    },
    {
      id: "upload",
      name: "Upload OpenAPI",
      desc: "Upload an OpenAPI 3.x file from your machine.",
      icon: (
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12" />
        </svg>
      ),
      pick: { kind: "openapi_upload" as const },
    },
    {
      id: "bareurl",
      name: "Bare API URL",
      desc: "Any HTTP API. Harnex probes paths and auth options.",
      icon: (
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
          <path d="M10 13a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-1 1" />
          <path d="M14 11a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l1-1" />
        </svg>
      ),
      pick: { kind: "bare_url" as const },
    },
  ];

  const activeTile = tiles.find((t) => t.id === picked);
  const choice: WizardChoice | null = activeTile?.pick ?? null;

  const tileLabel = (kind: WizardChoice["kind"]): string => {
    switch (kind) {
      case "builtin":
        return activeTile?.name ?? "—";
      case "openapi_url":
        return "OpenAPI URL";
      case "openapi_upload":
        return "Upload OpenAPI";
      case "bare_url":
        return "Bare API URL";
    }
  };

  const onFormState = (next: WizardFormState | null) => {
    setFormState(next);
    setTestResult(null); // any change invalidates the previous probe
  };

  const handleCreate = () => {
    if (formState && formState.valid) {
      create.mutate(formState);
    }
  };

  return (
    <div className="wizard-shell">
      {/* Breadcrumb */}
      <div className="responsive-toolbar" style={{ fontSize: 12 }}>
        <button className="btn btn-ghost btn-sm" onClick={() => void navigate({ to: "/connections" })}>
          {Ic.back} Back
        </button>
        <span style={{ color: "var(--muted)" }}>Connections</span>
        <span style={{ color: "var(--muted)" }}>/</span>
        <span>New connection</span>
      </div>

      {/* Stepper — completed / current / upcoming use distinct tokens in both themes */}
      <div className="wizard-stepper">
        {[
          { n: 1, label: "Choose connector" },
          { n: 2, label: "Configure" },
          { n: 3, label: "Review" },
        ].map((s, i, arr) => {
          const isComplete = step > s.n;
          const isCurrent = step === s.n;
          const isUpcoming = step < s.n;

          const circleStyle: React.CSSProperties = {
            width: 22,
            height: 22,
            borderRadius: 999,
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 11,
            fontWeight: 600,
            flexShrink: 0,
            ...(isUpcoming
              ? {
                  background: "var(--surface)",
                  color: "var(--muted)",
                  border: "1px solid var(--border)",
                }
              : isCurrent
                ? {
                    background: "var(--surface)",
                    color: "var(--ink)",
                    border: "2px solid var(--accent)",
                    boxShadow: "0 0 0 3px var(--accent-soft)",
                  }
                : {
                    background: "var(--green-soft)",
                    color: "var(--green)",
                    border: "1px solid var(--green-border)",
                  }),
          };

          return (
            <div key={s.n} style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <span style={circleStyle}>
                  {isComplete ? (
                    <span style={{ display: "inline-flex", color: "var(--green)" }}>{Ic.check}</span>
                  ) : (
                    s.n
                  )}
                </span>
                <span
                  style={{
                    fontSize: 12.5,
                    color: isUpcoming ? "var(--muted)" : "var(--ink)",
                    fontWeight: isCurrent ? 600 : isComplete ? 500 : 400,
                  }}
                >
                  {s.label}
                </span>
              </div>
              {i < arr.length - 1 && (
                <span
                  className="wizard-stepper-link"
                  style={{
                    background: step > s.n ? "var(--green)" : "var(--border)",
                    opacity: step > s.n ? 0.55 : 1,
                  }}
                />
              )}
            </div>
          );
        })}
      </div>

      {step === 1 && (
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          <div>
            <h2 className="h-display" style={{ fontSize: 22, margin: "8px 0 4px", fontWeight: 500 }}>
              Choose a <span className="serif-i">connector</span>
            </h2>
            <p style={{ fontSize: 13, color: "var(--slate)", margin: 0 }}>
              Pick a built-in connector or bring your own spec.
            </p>
          </div>
          <div className="wizard-tile-grid">
            {tiles.map((t) => (
              <button
                key={t.id}
                onClick={() => {
                  if (picked !== t.id) {
                    setPicked(t.id);
                    setFormState(null);
                    setTestResult(null);
                  }
                }}
                style={{
                  display: "flex",
                  alignItems: "flex-start",
                  gap: 14,
                  padding: 16,
                  textAlign: "left",
                  border: `1px solid ${picked === t.id ? "var(--ink)" : "var(--border)"}`,
                  borderRadius: 8,
                  background: "var(--surface)",
                  cursor: "pointer",
                  boxShadow: picked === t.id ? "0 0 0 3px rgba(10,10,10,0.06)" : "none",
                }}
              >
                <div
                  style={{
                    width: 44,
                    height: 44,
                    borderRadius: 6,
                    background: "var(--bg-alt)",
                    border: "1px solid var(--border)",
                    display: "inline-flex",
                    alignItems: "center",
                    justifyContent: "center",
                    color: "var(--ink)",
                    flexShrink: 0,
                  }}
                >
                  {t.icon}
                </div>
                <div className="min-w-0" style={{ flex: 1 }}>
                  <div style={{ fontSize: 14, fontWeight: 500, marginBottom: 3 }}>{t.name}</div>
                  <div style={{ fontSize: 12, color: "var(--muted)", lineHeight: 1.5 }}>
                    {t.desc}
                  </div>
                </div>
                {picked === t.id && <span style={{ color: "var(--accent)" }}>{Ic.check}</span>}
              </button>
            ))}
          </div>
          <div className="wizard-actions" style={{ justifyContent: "flex-end", marginTop: 8 }}>
            <button
              className="btn btn-primary"
              disabled={!picked}
              onClick={() => setStep(2)}
              style={{ opacity: picked ? 1 : 0.5 }}
            >
              Continue {Ic.arrow}
            </button>
          </div>
        </div>
      )}

      {step === 2 && choice && (
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <div>
            <h2 className="h-display" style={{ fontSize: 22, margin: "0 0 4px", fontWeight: 500 }}>
              Configure <span className="serif-i">{tileLabel(choice.kind)}</span>
            </h2>
            <p style={{ fontSize: 13, color: "var(--slate)", margin: 0 }}>
              Harnex will validate and index this connection.
            </p>
          </div>

          {choice.kind === "builtin" && (
            <BuiltinConnectorForm
              connectorKey={choice.connectorKey}
              embedded
              submitting={create.isPending}
              onStateChange={onFormState}
            />
          )}
          {choice.kind === "openapi_url" && (
            <OpenApiUrlForm
              embedded
              submitting={create.isPending}
              onStateChange={onFormState}
            />
          )}
          {choice.kind === "openapi_upload" && (
            <OpenApiUploadForm
              embedded
              submitting={create.isPending}
              onStateChange={onFormState}
            />
          )}
          {choice.kind === "bare_url" && (
            <BareUrlForm
              embedded
              submitting={create.isPending}
              onStateChange={onFormState}
            />
          )}

          {testResult && (
            <AlertBox variant={testResult.ok ? "info" : "red"}>
              <div style={{ display: "flex", gap: 12, alignItems: "flex-start" }}>
                <span style={{ display: "inline-flex", flexShrink: 0, paddingTop: 2 }}>
                  {testResult.ok ? Ic.check : Ic.warning}
                </span>
                <div
                  style={{
                    flex: 1,
                    minWidth: 0,
                    display: "flex",
                    flexDirection: "column",
                    gap: 6,
                  }}
                >
                  <strong style={{ fontSize: 13 }}>
                    {testResult.ok ? "Connection ok" : "Connection failed"}
                    {testResult.http_status !== null && ` · HTTP ${testResult.http_status}`}
                  </strong>
                  <span className="mono" style={{ fontSize: 11.5, color: "var(--muted)" }}>
                    {testResult.method} {testResult.url}
                  </span>
                  <span style={{ fontSize: 12 }}>{testResult.message}</span>
                  {testResult.ok && (
                    <ProbeMetadataBlock metadata={testResult.metadata ?? {}} />
                  )}
                </div>
              </div>
            </AlertBox>
          )}

          {test.error && !testResult && (
            <AlertBox variant="red">
              <span style={{ display: "inline-flex" }}>{Ic.warning}</span>
              <div>Test failed to run: {String(test.error)}</div>
            </AlertBox>
          )}

          <div className="wizard-actions" style={{ marginTop: 6 }}>
            <button className="btn btn-ghost" onClick={() => setStep(1)}>
              {Ic.back} Back
            </button>
            <span className="toolbar-spacer" />
            <button
              className="btn btn-secondary"
              onClick={() => formState && test.mutate(formState)}
              disabled={!formState || !formState.valid || test.isPending}
              title={
                !formState?.valid
                  ? "Fill in the required fields first"
                  : "Probe the API to verify auth"
              }
            >
              {test.isPending ? "Testing…" : "Test connection"}
            </button>
            <button
              className="btn btn-primary"
              disabled={!formState || !formState.valid}
              onClick={() => setStep(3)}
            >
              Continue {Ic.arrow}
            </button>
          </div>
        </div>
      )}

      {step === 3 && choice && formState && (
        <div className="card wizard-card-pad" style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <h2 className="h-display" style={{ fontSize: 22, margin: 0, fontWeight: 500 }}>
            Review &amp; <span className="serif-i">create</span>
          </h2>

          <ReviewGrid>
            <ReviewRow k="connector" v={tileLabel(choice.kind)} />
            <ReviewRow k="name" v={formState.payload.name || "—"} mono />
            <ReviewRow
              k="mode"
              v={<span className="badge badge-slate">{formState.payload.mode}</span>}
            />
            {formState.payload.base_url && (
              <ReviewRow k="base url" v={formState.payload.base_url} mono />
            )}
            {formState.payload.spec_url && (
              <ReviewRow k="spec url" v={formState.payload.spec_url} mono />
            )}
            {formState.file && (
              <ReviewRow
                k="spec file"
                v={`${formState.file.name} (${Math.round(formState.file.size / 1024)} KB)`}
                mono
              />
            )}
            <ReviewRow k="auth method" v={formState.summary.authMethodLabel} />
            {formState.summary.secretSummary !== null && (
              <ReviewRow
                k="credential"
                v={<span className="mono">{formState.summary.secretSummary}</span>}
              />
            )}
            {formState.summary.isOAuth && (
              <ReviewRow
                k="oauth"
                v={
                  <span style={{ color: "var(--accent-ink)" }}>
                    Will redirect to {formState.summary.oauthProvider ?? "provider"} after creation
                  </span>
                }
              />
            )}
            <ReviewRow
              k="indexing"
              v={<span style={{ color: "var(--accent)" }}>queued — starts after create</span>}
            />
          </ReviewGrid>

          {testResult && (
            <AlertBox variant={testResult.ok ? "info" : "amber"}>
              <div style={{ display: "flex", gap: 12, alignItems: "flex-start" }}>
                <span style={{ display: "inline-flex", flexShrink: 0, paddingTop: 2 }}>
                  {testResult.ok ? Ic.check : Ic.warning}
                </span>
                <div
                  style={{
                    flex: 1,
                    minWidth: 0,
                    display: "flex",
                    flexDirection: "column",
                    gap: 6,
                  }}
                >
                  <div style={{ fontSize: 13 }}>
                    <strong>{testResult.ok ? "Probe passed" : "Probe warning"}</strong>
                    {" — "}
                    {testResult.message}
                  </div>
                  {testResult.ok && !!testResult.url && (
                    <span className="mono" style={{ fontSize: 11.5, color: "var(--muted)" }}>
                      {testResult.method} {testResult.url}
                    </span>
                  )}
                  {testResult.ok && (
                    <ProbeMetadataBlock metadata={testResult.metadata ?? {}} />
                  )}
                </div>
              </div>
            </AlertBox>
          )}

          <AlertBox variant="info">
            <span style={{ display: "inline-flex" }}>{Ic.info}</span>
            <span>
              Harnex will start indexing immediately. Most APIs are fully indexed within 60 seconds.
            </span>
          </AlertBox>

          {create.error && (
            <AlertBox variant="red">
              <span style={{ display: "inline-flex" }}>{Ic.warning}</span>
              <div>Failed to create connection: {String(create.error)}</div>
            </AlertBox>
          )}

          <div className="wizard-actions">
            <button className="btn btn-ghost" onClick={() => setStep(2)}>
              {Ic.back} Back
            </button>
            <span className="toolbar-spacer" />
            <button
              className="btn btn-accent"
              onClick={handleCreate}
              disabled={create.isPending || !formState.valid}
            >
              {create.isPending ? "Creating…" : "Create connection"}
            </button>
          </div>
        </div>
      )}

      {step === 3 && (!choice || !formState) && (
        <AlertBox variant="amber">
          <span style={{ display: "inline-flex" }}>{Ic.warning}</span>
          <div>Form state is missing — please go back and fill in the form.</div>
        </AlertBox>
      )}
    </div>
  );
}

function normalizeProbeResult(result: ConnectionTestResult): ConnectionTestResult {
  const metadata: Record<string, string> = {};
  const raw = result.metadata;
  if (raw && typeof raw === "object" && !Array.isArray(raw)) {
    for (const [k, v] of Object.entries(raw)) {
      if (v == null || v === "") continue;
      const s = typeof v === "string" ? v.trim() : String(v).trim();
      if (s) metadata[k] = s;
    }
  }
  return { ...result, metadata };
}

function ProbeMetadataBlock({ metadata }: { metadata: Record<string, string> }) {
  if (Object.keys(metadata).length === 0) return null;
  return (
    <div
      style={{
        borderTop: "1px solid var(--border)",
        marginTop: 4,
        paddingTop: 10,
        display: "flex",
        flexDirection: "column",
        gap: 8,
      }}
    >
      <div style={{ fontSize: 11.5, fontWeight: 600, color: "var(--ink)" }}>
        Connection details
      </div>
      <ReviewGrid>
        {Object.entries(metadata).map(([key, value]) => (
          <ReviewRow key={key} k={key} v={value} mono />
        ))}
      </ReviewGrid>
    </div>
  );
}

function ReviewGrid({ children }: { children: React.ReactNode }) {
  return (
    <div
      style={{
        background: "var(--bg-alt)",
        border: "1px solid var(--border)",
        borderRadius: 8,
        padding: 16,
      }}
    >
      <div className="wizard-review-grid">
        {children}
      </div>
    </div>
  );
}

function ReviewRow({
  k,
  v,
  mono,
}: {
  k: string;
  v: React.ReactNode;
  mono?: boolean;
}) {
  return (
    <>
      <span style={{ color: "var(--muted)", fontFamily: "var(--font-mono)", fontSize: 11.5 }}>
        {k}
      </span>
      <span
        style={{
          fontFamily: mono ? "var(--font-mono)" : undefined,
          fontSize: mono ? 12 : 12.5,
          color: "var(--ink)",
          wordBreak: "break-all",
        }}
      >
        {v}
      </span>
    </>
  );
}
