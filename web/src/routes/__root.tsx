import type { QueryClient } from "@tanstack/react-query";
import { Link, Outlet, createRootRouteWithContext } from "@tanstack/react-router";

import { HarnexLogo } from "@/components/HarnexLogo";
import type { AuthState } from "@/lib/auth";

export interface RouterContext {
  auth: AuthState;
  queryClient: QueryClient;
}

export const Route = createRootRouteWithContext<RouterContext>()({
  component: RootLayout,
  notFoundComponent: NotFoundPage,
});

function RootLayout() {
  return <Outlet />;
}

function NotFoundPage() {
  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "var(--bg)",
        padding: "32px 20px",
        fontFamily: "var(--font-sans)",
        color: "var(--ink)",
      }}
    >
      <div
        style={{
          maxWidth: 460,
          width: "100%",
          background: "var(--surface)",
          border: "1px solid var(--border)",
          borderRadius: 12,
          padding: "32px 28px",
          boxShadow: "var(--shadow-sm)",
          textAlign: "center",
        }}
      >
        <div style={{ display: "flex", justifyContent: "center", marginBottom: 24 }}>
          <HarnexLogo size={28} />
        </div>
        <div
          className="mono"
          style={{
            fontSize: 11,
            letterSpacing: "0.08em",
            color: "var(--muted)",
            textTransform: "uppercase",
            marginBottom: 8,
          }}
        >
          Error 404
        </div>
        <h1
          style={{
            fontSize: 22,
            fontWeight: 600,
            margin: "0 0 8px",
            letterSpacing: "-0.01em",
          }}
        >
          Page not found
        </h1>
        <p style={{ fontSize: 13.5, color: "var(--slate)", margin: "0 0 24px", lineHeight: 1.5 }}>
          The page you’re looking for doesn’t exist or has been moved.
        </p>
        <div
          style={{
            display: "flex",
            gap: 8,
            justifyContent: "center",
            flexWrap: "wrap",
          }}
        >
          <Link to="/dashboard" className="btn btn-accent btn-sm">
            Go to dashboard
          </Link>
          <Link to="/home" className="btn btn-ghost btn-sm">
            Visit homepage
          </Link>
        </div>
      </div>
    </div>
  );
}
