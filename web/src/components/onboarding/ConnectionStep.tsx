import { useState } from "react";

import { FormActions } from "./FormActions";
import { Marks } from "./marks";
import { POPULAR_CONNECTIONS, type ConnectionState } from "./types";

interface ConnectionStepProps {
  value: ConnectionState;
  onChange: (next: ConnectionState) => void;
  onContinue: () => void;
  onBack?: () => void;
  onSkip: () => void;
  busy?: boolean;
  serverError?: string | null;
}

export function ConnectionStep({
  value,
  onChange,
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
  const selectedName = selected
    ? POPULAR_CONNECTIONS.find((c) => c.key === selected)?.name
    : null;

  return (
    <div className="ob-step-body">
      <div className="ob-kicker mono">
        STEP 03 · CONNECTION <span className="ob-kicker-opt">· OPTIONAL</span>
      </div>
      <h1 className="ob-title">
        Add your <span className="serif-i">first</span> connection.
      </h1>
      <p className="ob-sub">
        Pick a tool your agents will reach for most. We&apos;ll generate typed handlers and a
        sandbox in your console — no keys required to explore.
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

      <div className="ob-conn-grid">
        {filtered.map((c) => {
          const active = selected === c.key;
          return (
            <button
              key={c.key}
              type="button"
              className={`ob-conn${active ? " is-active" : ""}`}
              onClick={() => onChange({ ...value, connection: active ? null : c.key })}
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
