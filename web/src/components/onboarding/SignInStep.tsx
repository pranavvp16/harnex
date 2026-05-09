import { useState } from "react";

export type Provider = "google" | "github" | "email";

interface SignInStepProps {
  onSignIn: (provider: Provider) => void | Promise<void>;
  onSignInExisting?: () => void;
}

export function SignInStep({ onSignIn, onSignInExisting }: SignInStepProps) {
  const [loadingProvider, setLoadingProvider] = useState<Provider | null>(null);

  const trigger = async (provider: Provider) => {
    setLoadingProvider(provider);
    try {
      await onSignIn(provider);
    } finally {
      setLoadingProvider(null);
    }
  };

  return (
    <div className="ob-step-body">
      <div className="ob-kicker">WELCOME</div>
      <h1 className="ob-title">
        Let&apos;s get your <span className="serif-i">harness</span> wired up.
      </h1>
      <p className="ob-sub">
        Sign in to provision a Harnex workspace. We&apos;ll set up your first connection
        together — it takes about a minute.
      </p>

      <div className="ob-providers">
        <button
          type="button"
          className={`ob-provider${loadingProvider === "google" ? " is-loading" : ""}`}
          onClick={() => void trigger("google")}
          disabled={loadingProvider !== null}
        >
          <span className="ob-provider-mark">
            <svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true">
              <path
                fill="#4285F4"
                d="M21.6 12.2c0-.7-.06-1.4-.18-2H12v3.83h5.4a4.6 4.6 0 0 1-2 3.04v2.5h3.23c1.9-1.74 2.97-4.32 2.97-7.37z"
              />
              <path
                fill="#34A853"
                d="M12 22c2.7 0 4.96-.9 6.62-2.43l-3.23-2.5c-.9.6-2.05.96-3.39.96-2.6 0-4.81-1.76-5.6-4.13H3.07v2.6A10 10 0 0 0 12 22z"
              />
              <path
                fill="#FBBC05"
                d="M6.4 13.9a6 6 0 0 1 0-3.8V7.5H3.07a10 10 0 0 0 0 9z"
              />
              <path
                fill="#EA4335"
                d="M12 5.96c1.47 0 2.78.5 3.82 1.5l2.86-2.86A10 10 0 0 0 3.07 7.5L6.4 10.1c.79-2.37 3-4.13 5.6-4.13z"
              />
            </svg>
          </span>
          <span className="ob-provider-label">Continue with Google</span>
          {loadingProvider === "google" && <span className="ob-spinner" />}
        </button>

        <button
          type="button"
          className={`ob-provider${loadingProvider === "github" ? " is-loading" : ""}`}
          onClick={() => void trigger("github")}
          disabled={loadingProvider !== null}
        >
          <span className="ob-provider-mark" style={{ color: "var(--ink)" }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
              <path d="M12 2C6.5 2 2 6.6 2 12.2c0 4.5 2.87 8.3 6.85 9.65.5.1.68-.22.68-.49 0-.24-.01-.88-.01-1.72-2.78.62-3.37-1.36-3.37-1.36-.46-1.18-1.12-1.5-1.12-1.5-.92-.64.07-.62.07-.62 1.01.07 1.55 1.06 1.55 1.06.9 1.57 2.37 1.12 2.95.85.09-.66.35-1.12.64-1.38-2.22-.26-4.55-1.13-4.55-5.03 0-1.11.39-2.02 1.03-2.73-.1-.26-.45-1.3.1-2.7 0 0 .84-.27 2.75 1.04A9.4 9.4 0 0 1 12 6.96c.85 0 1.7.12 2.5.34 1.91-1.31 2.75-1.04 2.75-1.04.55 1.4.2 2.44.1 2.7.64.71 1.03 1.62 1.03 2.73 0 3.91-2.34 4.77-4.57 5.02.36.31.68.92.68 1.86 0 1.34-.01 2.42-.01 2.75 0 .27.18.6.69.49C19.13 20.5 22 16.7 22 12.2 22 6.6 17.5 2 12 2z" />
            </svg>
          </span>
          <span className="ob-provider-label">Continue with GitHub</span>
          {loadingProvider === "github" && <span className="ob-spinner" />}
        </button>

        <button
          type="button"
          className={`ob-provider${loadingProvider === "email" ? " is-loading" : ""}`}
          onClick={() => void trigger("email")}
          disabled={loadingProvider !== null}
        >
          <span className="ob-provider-mark" style={{ color: "var(--ink)" }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <rect x="3" y="5" width="18" height="14" rx="2" />
              <path d="m3 7 9 6 9-6" />
            </svg>
          </span>
          <span className="ob-provider-label">Continue with email</span>
          {loadingProvider === "email" && <span className="ob-spinner" />}
        </button>
      </div>

      {onSignInExisting && (
        <p className="ob-signin-cta">
          Already have an account?{" "}
          <button
            type="button"
            className="ob-signin-link ob-signin-button"
            onClick={onSignInExisting}
          >
            Sign in
          </button>
        </p>
      )}

      <div className="ob-fineprint">
        By continuing you agree to the <a href="#">Terms</a> and <a href="#">Privacy</a> policy.
        We never request scopes we don&apos;t use; you can revoke access from your provider at any
        time.
      </div>
    </div>
  );
}
