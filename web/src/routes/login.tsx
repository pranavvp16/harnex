import { Link, createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState } from "react";

import { Button } from "@/components/ui/Button";
import { Field } from "@/components/ui/Field";
import { Input } from "@/components/ui/Input";
import { AuthError, useAuth, type IdpHint } from "@/lib/auth";

export const Route = createFileRoute("/login")({
  component: LoginPage,
});

function LoginPage() {
  const auth = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [providerBusy, setProviderBusy] = useState<IdpHint | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await auth.signInWithPassword({ email: email.trim(), password });
      void navigate({ to: "/" });
    } catch (err) {
      setError(err instanceof AuthError ? err.message : "Sign in failed");
    } finally {
      setBusy(false);
    }
  };

  const handleProvider = async (idpHint: IdpHint) => {
    setError(null);
    setProviderBusy(idpHint);
    try {
      await auth.signIn({ idpHint, returnTo: "/" });
    } catch (err) {
      setProviderBusy(null);
      setError(err instanceof Error ? err.message : "Provider sign-in failed");
    }
  };

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center gap-6 px-6 py-10">
      <header className="text-center">
        <h1 className="text-2xl font-semibold text-slate-900">Sign in to Harnex</h1>
        <p className="mt-1 text-sm text-slate-600">
          Welcome back. Use email or your social account.
        </p>
      </header>

      <form onSubmit={(e) => void handleSubmit(e)} className="flex flex-col gap-4">
        <Field label="Email" htmlFor="login-email">
          <Input
            id="login-email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </Field>
        <Field label="Password" htmlFor="login-password">
          <Input
            id="login-password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </Field>
        {error && (
          <p style={{ fontSize: 12.5, color: "var(--red)", margin: 0 }}>{error}</p>
        )}
        <Button type="submit" disabled={busy || providerBusy !== null}>
          {busy ? "Signing in…" : "Sign in"}
        </Button>
      </form>

      <div className="flex items-center gap-3 text-xs uppercase tracking-wide text-slate-400">
        <span className="h-px flex-1 bg-slate-200" />
        <span>or continue with</span>
        <span className="h-px flex-1 bg-slate-200" />
      </div>

      <div className="flex flex-col gap-2">
        <Button
          variant="secondary"
          disabled={busy || providerBusy !== null}
          onClick={() => void handleProvider("google")}
        >
          {providerBusy === "google" ? "Redirecting…" : "Continue with Google"}
        </Button>
        <Button
          variant="secondary"
          disabled={busy || providerBusy !== null}
          onClick={() => void handleProvider("github")}
        >
          {providerBusy === "github" ? "Redirecting…" : "Continue with GitHub"}
        </Button>
      </div>

      <p className="text-center text-sm text-slate-600">
        Don&apos;t have an account?{" "}
        <Link to="/onboarding" className="text-slate-900 underline">
          Sign up
        </Link>
      </p>
    </main>
  );
}
