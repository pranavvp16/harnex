import { useState } from "react";

import { FormActions } from "./FormActions";

export interface EmailSignInValue {
  email: string;
  password: string;
}

interface EmailSignInStepProps {
  value: EmailSignInValue;
  onChange: (next: EmailSignInValue) => void;
  onContinue: () => void;
  onBack?: () => void;
  onSwitchToSignUp?: () => void;
  busy?: boolean;
  serverError?: string | null;
}

export function EmailSignInStep({
  value,
  onChange,
  onContinue,
  onBack,
  onSwitchToSignUp,
  busy,
  serverError,
}: EmailSignInStepProps) {
  const [touched, setTouched] = useState(false);

  const emailOk = /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(value.email.trim());
  const passwordOk = value.password.length > 0;
  const allOk = emailOk && passwordOk;

  return (
    <div className="ob-step-body">
      <div className="ob-kicker mono">SIGN IN</div>
      <h1 className="ob-title">
        Welcome <span className="serif-i">back.</span>
      </h1>
      <p className="ob-sub">
        Enter the email and password you signed up with to pick up where you left off.
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
          <span className="ob-field-label">Email</span>
          <input
            className="input ob-input"
            type="email"
            value={value.email}
            onChange={(e) => onChange({ ...value, email: e.target.value })}
            placeholder="you@company.com"
            autoComplete="email"
            autoFocus
            spellCheck={false}
          />
          {touched && !emailOk && (
            <span className="ob-error">Enter a valid email address.</span>
          )}
        </label>

        <label className="ob-field">
          <span className="ob-field-label">Password</span>
          <input
            className="input ob-input"
            type="password"
            value={value.password}
            onChange={(e) => onChange({ ...value, password: e.target.value })}
            autoComplete="current-password"
          />
          {touched && !passwordOk && (
            <span className="ob-error">Enter your password.</span>
          )}
        </label>

        {serverError && <span className="ob-error">{serverError}</span>}

        <FormActions
          onBack={onBack}
          primary="Sign in"
          disabled={!allOk}
          busy={busy}
        />
      </form>

      {onSwitchToSignUp && (
        <p className="ob-signin-cta" style={{ marginTop: 16 }}>
          New to Harnex?{" "}
          <button type="button" className="ob-signin-link ob-signin-button" onClick={onSwitchToSignUp}>
            Create an account
          </button>
        </p>
      )}
    </div>
  );
}
