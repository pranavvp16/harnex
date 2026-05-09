import { useEffect, useState } from "react";

import { useApi } from "@/lib/useApi";

import { FormActions } from "./FormActions";
import { TEAM_SIZES, type OrgState } from "./types";

const slugFromName = (name: string): string =>
  name
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");

type SlugStatus = "idle" | "checking" | "available" | "taken" | "invalid";

interface OrgStepProps {
  value: OrgState;
  onChange: (next: OrgState) => void;
  onContinue: () => void;
  onBack?: () => void;
  busy?: boolean;
  serverError?: string | null;
}

export function OrgStep({
  value,
  onChange,
  onContinue,
  onBack,
  busy,
  serverError,
}: OrgStepProps) {
  const api = useApi();
  const [touched, setTouched] = useState(false);
  const [slugStatus, setSlugStatus] = useState<SlugStatus>("idle");

  const slug = slugFromName(value.orgName);
  const ok = value.orgName.trim().length >= 2 && slug.length >= 2;

  useEffect(() => {
    if (slug.length < 2) {
      setSlugStatus("invalid");
      return;
    }
    let cancelled = false;
    setSlugStatus("checking");
    const handle = window.setTimeout(() => {
      api
        .checkTenantSlug(slug)
        .then((res) => {
          if (cancelled) return;
          setSlugStatus(res.available ? "available" : "taken");
        })
        .catch(() => {
          if (cancelled) return;
          setSlugStatus("idle");
        });
    }, 350);
    return () => {
      cancelled = true;
      window.clearTimeout(handle);
    };
  }, [slug, api]);

  const statusBadge = (() => {
    if (!slug) return null;
    if (slugStatus === "checking") {
      return (
        <span className="ob-helper-status ob-helper-status-busy">
          <span className="ob-dot ob-dot-busy" /> checking
        </span>
      );
    }
    if (slugStatus === "taken") {
      return (
        <span className="ob-helper-status ob-helper-status-bad">
          <span className="ob-dot ob-dot-bad" /> taken
        </span>
      );
    }
    if (slugStatus === "available") {
      return (
        <span className="ob-helper-status">
          <span className="ob-dot ob-dot-ok" /> available
        </span>
      );
    }
    return null;
  })();

  return (
    <div className="ob-step-body">
      <div className="ob-kicker mono">STEP 02 · WORKSPACE</div>
      <h1 className="ob-title">
        Name your <span className="serif-i">organization.</span>
      </h1>
      <p className="ob-sub">
        Workspaces hold your connections, API keys, and execution history. One per team, usually.
      </p>

      <form
        className="ob-form"
        onSubmit={(e) => {
          e.preventDefault();
          setTouched(true);
          if (ok && slugStatus !== "taken" && !busy) onContinue();
        }}
      >
        <label className="ob-field">
          <span className="ob-field-label">Organization name</span>
          <input
            className="input ob-input"
            value={value.orgName}
            onChange={(e) => onChange({ ...value, orgName: e.target.value })}
            placeholder="e.g. Acme AI Lab"
            autoFocus
            spellCheck={false}
          />
          <div className="ob-helper">
            <span className="mono ob-helper-pre">harnex.dev/</span>
            <span className="mono ob-helper-slug">{slug || "your-org"}</span>
            {statusBadge}
          </div>
          {touched && !ok && (
            <span className="ob-error">Choose a name with at least two characters.</span>
          )}
        </label>

        <fieldset className="ob-field ob-fieldset">
          <legend className="ob-field-label">Team size</legend>
          <div className="ob-segments">
            {TEAM_SIZES.map((s) => (
              <label key={s} className={`ob-segment${value.teamSize === s ? " is-active" : ""}`}>
                <input
                  type="radio"
                  name="size"
                  value={s}
                  checked={value.teamSize === s}
                  onChange={() => onChange({ ...value, teamSize: s })}
                />
                <span>{s}</span>
              </label>
            ))}
          </div>
        </fieldset>

        {serverError && <div className="alert alert-red">{serverError}</div>}

        <FormActions
          onBack={onBack}
          primary="Continue"
          disabled={!ok || slugStatus === "taken"}
          busy={busy}
        />
      </form>
    </div>
  );
}
