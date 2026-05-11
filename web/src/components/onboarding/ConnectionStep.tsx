import { useState } from "react";

import type { MarkKey } from "./marks";
import { FormActions } from "./FormActions";
import { Marks } from "./marks";
import {
  POPULAR_CONNECTIONS,
  wireLabelsForConnector,
  type ConnectionState,
} from "./types";

interface ConnectionStepProps {
  value: ConnectionState;
  onChange: (next: ConnectionState) => void;
  /** Hover from grid — previews orbit labels & detail card without committing selection. */
  previewConnector?: MarkKey | null;
  onHoverConnectorChange?: (key: MarkKey | null) => void;
  onContinue: () => void;
  onBack?: () => void;
  onSkip: () => void;
  busy?: boolean;
  serverError?: string | null;
}

export function ConnectionStep({
  value,
  onChange,
  previewConnector,
  onHoverConnectorChange,
  onContinue,
  onBack,
  onSkip,
  busy,
  serverError,
}: ConnectionStepProps) {
  const [search, setSearch] = useState("");
  const filtered = POPULAR_CONNECTIONS.filter(
    (c) =>
      c.name.toLowerCase().includes(search.toLowerCase()) ||
      c.kind.toLowerCase().includes(search.toLowerCase()),
  );
  const selected = value.connection;
  const selectedDetails = selected
    ? POPULAR_CONNECTIONS.find((c) => c.key === selected)
    : undefined;
  const selectedName = selectedDetails?.name;
  const focusKey = previewConnector ?? selected;
  const focusDetails = focusKey
    ? POPULAR_CONNECTIONS.find((c) => c.key === focusKey)
    : undefined;
  const previewLines = wireLabelsForConnector(focusKey).slice(0, 5);

  return (
    <div className="ob-step-body">
      <div className="ob-kicker mono">
        STEP 03 · CONNECTION <span className="ob-kicker-opt">· OPTIONAL</span>
      </div>
      <h1 className="ob-title">
        Add your <span className="serif-i">first</span> connection.
      </h1>
      <p className="ob-sub">
        Pick a tool your agents will reach for most. We&apos;ll generate typed handlers and a sandbox
        in your console — no keys required to explore.
      </p>

      <div className="ob-search">
        <svg
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          aria-hidden="true"
        >
          <circle cx="11" cy="11" r="7" />
          <path d="m20 20-3.5-3.5" />
        </svg>
        <input
          className="input ob-input"
          placeholder="Search connectors…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      <div
        className="ob-conn-grid"
        onMouseLeave={() => onHoverConnectorChange?.(null)}
      >
        {filtered.map((c) => {
          const active = selected === c.key;
          return (
            <button
              key={c.key}
              type="button"
              className={`ob-conn${active ? " is-active" : ""}`}
              onMouseEnter={() => onHoverConnectorChange?.(c.key)}
              onClick={() => {
                if (active) {
                  onChange({ connection: null, displayName: "" });
                } else {
                  const nameDefault =
                    POPULAR_CONNECTIONS.find((x) => x.key === c.key)?.name ?? "Connection";
                  onChange({
                    connection: c.key,
                    displayName: nameDefault,
                  });
                }
              }}
            >
              <span className="ob-conn-mark">{Marks[c.key]}</span>
              <span className="ob-conn-text">
                <span className="ob-conn-name">{c.name}</span>
                <span className="ob-conn-kind">{c.kind}</span>
              </span>
              <span className="ob-conn-check">
                {active && (
                  <svg
                    width="14"
                    height="14"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="3"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d="M5 12l5 5L20 7" />
                  </svg>
                )}
              </span>
            </button>
          );
        })}
        {filtered.length === 0 && (
          <div className="ob-conn-empty mono">
            No connector named &quot;{search}&quot;. Try GitHub, Postgres, OpenAI…
          </div>
        )}
      </div>

      {focusDetails && (
        <div className="ob-conn-detail">
          <div className="ob-conn-detail-head">
            <span className="ob-field-label mono">
              {focusKey === selected ? "Connection" : "Preview"}
            </span>
            <span className="ob-conn-detail-title">
              {focusDetails.name}
              <span className="ob-conn-detail-kind">{focusDetails.kind}</span>
            </span>
          </div>
          <p className="ob-conn-detail-copy">
            {selected === focusDetails.key
              ? "Name this connection for your workspace. You can add credentials after onboarding."
              : "Hover picks example routes on the constellation. Click to select and continue."}
          </p>
          {selected === focusDetails.key && (
            <div className="ob-field" style={{ marginTop: 4 }}>
              <label className="ob-field-label" htmlFor="ob-conn-display-name">
                Display name<span className="ob-field-opt">optional</span>
              </label>
              <input
                id="ob-conn-display-name"
                className="input ob-input"
                placeholder={focusDetails.name}
                value={value.displayName}
                onChange={(e) =>
                  onChange({
                    ...value,
                    connection: selected,
                    displayName: e.target.value,
                  })
                }
                autoComplete="off"
              />
            </div>
          )}
          <div className="ob-conn-detail-routes mono" aria-label="Sample API routes">
            {previewLines.map((line) => (
              <span key={line} className="ob-conn-detail-route-chip">
                {line}
              </span>
            ))}
          </div>
        </div>
      )}

      {serverError && <div className="alert alert-red" style={{ marginTop: 12 }}>{serverError}</div>}

      <FormActions
        onBack={onBack}
        primary={selected ? `Connect ${selectedName ?? "it"}` : "Continue"}
        secondary="Skip for now"
        onSecondary={onSkip}
        onContinue={onContinue}
        busy={busy}
      />
    </div>
  );
}
