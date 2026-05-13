import { createFileRoute } from "@tanstack/react-router";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { useAuth } from "@/lib/auth";

export const Route = createFileRoute("/_app/settings")({
  component: SettingsPage,
});

function SettingsPage() {
  const auth = useAuth();
  const email = auth.user?.email ?? "—";
  const name = auth.user?.full_name ?? "—";
  const sub = auth.user?.sub ?? "—";
  const tenantId = auth.devTenantId ?? "—";

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16, maxWidth: 720 }}>
      <header>
        <h1 style={{ fontSize: 22, fontWeight: 600, letterSpacing: "-0.02em", margin: 0 }}>
          Settings
        </h1>
        <p style={{ fontSize: 13.5, color: "var(--muted)", margin: "4px 0 0" }}>
          Account and workspace identity. More controls land here as we ship them.
        </p>
      </header>

      <Card>
        <div style={{ padding: 18, display: "flex", flexDirection: "column", gap: 14 }}>
          <h2 style={{ fontSize: 14, fontWeight: 600, margin: 0, color: "var(--ink)" }}>
            Account
          </h2>
          <Field label="Name" value={name} />
          <Field label="Email" value={email} />
          <Field label="Keycloak user id" value={sub} mono />
        </div>
      </Card>

      <Card>
        <div style={{ padding: 18, display: "flex", flexDirection: "column", gap: 14 }}>
          <h2 style={{ fontSize: 14, fontWeight: 600, margin: 0, color: "var(--ink)" }}>
            Active workspace
          </h2>
          <Field label="Tenant id" value={tenantId} mono />
          <p style={{ fontSize: 12, color: "var(--muted)", margin: 0 }}>
            Switching workspaces is coming soon. For now, log out and back in with a different
            account to change scope.
          </p>
        </div>
      </Card>

      <Card>
        <div style={{ padding: 18, display: "flex", flexDirection: "column", gap: 14 }}>
          <h2 style={{ fontSize: 14, fontWeight: 600, margin: 0, color: "var(--ink)" }}>
            Session
          </h2>
          <p style={{ fontSize: 12.5, color: "var(--muted)", margin: 0 }}>
            Sign out clears your session here and at the identity provider.
          </p>
          <div>
            <Button variant="secondary" onClick={() => void auth.signOut()}>
              Sign out
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}

function Field({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 3 }}>
      <span style={{ fontSize: 11.5, fontWeight: 500, color: "var(--slate)" }}>{label}</span>
      <span
        style={{
          fontSize: mono ? 12.5 : 13.5,
          fontFamily: mono ? "var(--font-mono)" : undefined,
          color: "var(--ink)",
          wordBreak: "break-all",
        }}
      >
        {value}
      </span>
    </div>
  );
}
