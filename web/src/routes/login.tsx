import { createFileRoute } from "@tanstack/react-router";
import { useEffect } from "react";

import { Button } from "@/components/ui/Button";
import { useAuth } from "@/lib/auth";

export const Route = createFileRoute("/login")({
  component: LoginPage,
});

function LoginPage() {
  const auth = useAuth();

  useEffect(() => {
    if (auth.status === "anonymous") {
      void auth.signIn();
    }
  }, [auth.status, auth]);

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col items-center justify-center gap-6 px-6 text-center">
      <h1 className="text-2xl font-semibold text-slate-900">Sign in to Harnex</h1>
      <p className="text-sm text-slate-600">Redirecting to Keycloak…</p>
      <Button onClick={() => void auth.signIn()}>Continue with Keycloak</Button>
    </main>
  );
}
