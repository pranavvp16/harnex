import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect } from "react";

import { useAuth } from "@/lib/auth";

export const Route = createFileRoute("/")({
  component: IndexGate,
});

/** `/` must never render blank: auth bootstrap stays `loading` until OIDC or dev-tenant resolves. */
function IndexGate() {
  const auth = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (auth.status === "authenticated") {
      void navigate({ to: "/dashboard", replace: true });
    } else if (auth.status === "anonymous") {
      void navigate({ to: "/home", replace: true });
    }
  }, [auth.status, navigate]);

  if (auth.status !== "loading") {
    return null;
  }

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "var(--bg)",
        color: "var(--muted)",
        fontFamily: "var(--font-sans)",
        fontSize: 13,
      }}
    >
      Loading…
    </div>
  );
}
