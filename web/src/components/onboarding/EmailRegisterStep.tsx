import { useState } from "react";

import { FormActions } from "./FormActions";

export interface EmailRegisterValue {
  fullName: string;
  email: string;
  password: string;
}

interface EmailRegisterStepProps {
  value: EmailRegisterValue;
  onChange: (next: EmailRegisterValue) => void;
  onContinue: () => void;
  onBack?: () => void;
  onSwitchToSignIn?: () => void;
  busy?: boolean;
  serverError?: string | null;
}

export function EmailRegisterStep({
  value,
  onChange,
  onContinue,
  onBack,
  onSwitchToSignIn,
  busy,
  serverError,
}: EmailRegisterStepProps) {
  const [touched, setTouched] = useState(false);

  const nameOk = value.fullName.trim().length >= 2;
  const emailOk = /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(value.email.trim());
  const passwordOk = value.password.length >= 8;
  const allOk = nameOk && emailOk && passwordOk;

  return (
    <div className="ob-step-body">
      <div className="ob-kicker mono">STEP 01 · CREATE ACCOUNT</div>
      <h1 className="ob-title">
        Set up your <span className="serif-i">credentials.</span>
      </h1>
      <p className="ob-sub">
        We&apos;ll create your account, then collect a couple of details for your workspace. You can
        change everything later from Settings.
      </p>

      <form
        className="ob-form"
        onSubmit={(e) => {
          e.preventDefault();
          setTouched(true);
          if (allOk) onContinue();
        }}
      >
        <label className="ob-field">
          <span className="ob-field-label">Full name</span>
          <input
            className="input ob-input"
            value={value.fullName}
            onChange={(e) => onChange({ ...value, fullName: e.target.value })}
            placeholder="e.g. Alex Reyes"
            autoComplete="name"
            autoFocus
            spellCheck={false}
          />
          {touched && !nameOk && (
            <span className="ob-error">Please enter at least two characters.</span>
          )}
        </label>

        <label className="ob-field">
          <span className="ob-field-label">Work email</span>
          <input
            className="input ob-input"
            type="email"
            value={value.email}
            onChange={(e) => onChange({ ...value, email: e.target.value })}
            placeholder="you@company.com"
            autoComplete="email"
            spellCheck={false}
          />
          {touched && !emailOk && (
            <span className="ob-error">Enter a valid email address.</span>
          )}
        </label>

        <label className="ob-field">
          <span className="ob-field-label">
            Password <span className="ob-field-opt">at least 8 characters</span>
          </span>
          <input
            className="input ob-input"
            type="password"
            value={value.password}
            onChange={(e) => onChange({ ...value, password: e.target.value })}
            autoComplete="new-password"
          />
          {touched && !passwordOk && (
            <span className="ob-error">Password must be at least 8 characters.</span>
          )}
        </label>

        {serverError && <span className="ob-error">{serverError}</span>}

        <FormActions
          onBack={onBack}
          primary="Create account"
          disabled={!allOk}
          busy={busy}
        />
      </form>

      {onSwitchToSignIn && (
        <p className="ob-signin-cta" style={{ marginTop: 16 }}>
          Already have an account?{" "}
          <button
            type="button"
            className="ob-signin-link ob-signin-button"
            onClick={onSwitchToSignIn}
          >
            Sign in
          </button>
        </p>
      )}
    </div>
  );
}
