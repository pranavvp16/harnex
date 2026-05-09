import { useState } from "react";

import { FormActions } from "./FormActions";
import type { ProfileState } from "./types";

interface ProfileStepProps {
  value: ProfileState;
  onChange: (next: ProfileState) => void;
  onContinue: () => void;
  onBack?: () => void;
}

export function ProfileStep({ value, onChange, onContinue, onBack }: ProfileStepProps) {
  const [touched, setTouched] = useState(false);
  const ok = value.fullName.trim().length >= 2;

  return (
    <div className="ob-step-body">
      <div className="ob-kicker mono">STEP 01 · PROFILE</div>
      <h1 className="ob-title">
        First, what should we <span className="serif-i">call you?</span>
      </h1>
      <p className="ob-sub">
        Your name appears on commits, audit logs, and shared playground sessions. You can change it
        later from Settings.
      </p>

      <form
        className="ob-form"
        onSubmit={(e) => {
          e.preventDefault();
          setTouched(true);
          if (ok) onContinue();
        }}
      >
        <label className="ob-field">
          <span className="ob-field-label">Full name</span>
          <input
            className="input ob-input"
            value={value.fullName}
            onChange={(e) => onChange({ ...value, fullName: e.target.value })}
            placeholder="e.g. Alex Reyes"
            autoFocus
            spellCheck={false}
          />
          {touched && !ok && (
            <span className="ob-error">Please enter at least two characters.</span>
          )}
        </label>

        <label className="ob-field">
          <span className="ob-field-label">
            Display handle <span className="ob-field-opt">optional</span>
          </span>
          <div className="ob-input-prefix">
            <span className="ob-prefix mono">@</span>
            <input
              className="input ob-input"
              value={value.handle}
              onChange={(e) =>
                onChange({
                  ...value,
                  handle: e.target.value.replace(/[^a-z0-9-]/gi, "").toLowerCase(),
                })
              }
              placeholder="alex"
              spellCheck={false}
            />
          </div>
        </label>

        <FormActions onBack={onBack} primary="Continue" disabled={!ok} />
      </form>
    </div>
  );
}
