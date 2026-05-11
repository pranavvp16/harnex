import {
  Link,
  Outlet,
  createFileRoute,
  redirect,
  useMatchRoute,
  useRouter,
} from "@tanstack/react-router";
import {
  BarChart2,
  Bell,
  BookOpen,
  ChevronDown,
  Key,
  LayoutDashboard,
  LogOut,
  Menu,
  Moon,
  Plug,
  Search,
  Settings,
  Sun,
  Zap,
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { HarnexLogo } from "@/components/HarnexLogo";
import { useAuth } from "@/lib/auth";
import { useApi } from "@/lib/useApi";
import { useTheme } from "@/lib/theme";

export const Route = createFileRoute("/_app")({
  beforeLoad: ({ context, location }) => {
    if (context.auth.status === "loading") return;
    if (context.auth.status !== "authenticated") {
      throw redirect({
        to: "/login",
        search: { returnTo: location.pathname },
      });
    }
    // Authenticated but no tenant yet — finish onboarding before showing
    // the workspace shell. Skips the redirect when /onboarding itself bounces
    // through here (it lives outside _app, so this only fires for /dashboard etc).
    if (!context.auth.devTenantId) {
      throw redirect({ to: "/onboarding" });
    }
  },
  component: AppShell,
});

const NAV = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/connections", label: "Connections", icon: Plug },
  { to: "/search", label: "Search", icon: Search },
  { to: "/api-keys", label: "API Keys", icon: Key },
  { to: "/executions", label: "Executions", icon: Zap },
  { to: "/usage", label: "Usage", icon: BarChart2 },
] as const;

const PAGE_TITLES = {
  "/dashboard": "Dashboard",
  "/connections": "Connections",
  "/search": "Search playground",
  "/api-keys": "API keys",
  "/executions": "Executions",
  "/usage": "Usage",
  "/style-guide": "Style guide",
} as const;

type ShellTitlePath = keyof typeof PAGE_TITLES;

/** Longer paths first so a hypothetical future `/foo`/`/foo-bar` pairing stays unambiguous */
const TITLE_MATCH_ORDER_BY_LENGTH: ShellTitlePath[] = (
  Object.keys(PAGE_TITLES) as ShellTitlePath[]
).sort((a, b) => b.length - a.length);

function shellPageTitle(matchRoute: ReturnType<typeof useMatchRoute>): string {
  if (matchRoute({ to: "/connections/new", fuzzy: false })) return "New connection";
  const connDetail = matchRoute({ to: "/connections/$id", fuzzy: false });
  if (
    connDetail &&
    typeof connDetail.id === "string" &&
    connDetail.id !== "new"
  ) {
    return "Connection";
  }

  for (const path of TITLE_MATCH_ORDER_BY_LENGTH) {
    if (matchRoute({ to: path, fuzzy: false })) return PAGE_TITLES[path];
  }

  return "Harnex";
}

const NAV_BREAKPOINT = "(max-width: 1023px)";

function useNarrowNav(): boolean {
  const [narrow, setNarrow] = useState(false);
  useEffect(() => {
    const mq = window.matchMedia(NAV_BREAKPOINT);
    const sync = () => setNarrow(mq.matches);
    sync();
    mq.addEventListener("change", sync);
    return () => mq.removeEventListener("change", sync);
  }, []);
  return narrow;
}

function AppShell() {
  const auth = useAuth();
  const router = useRouter();
  const matchRoute = useMatchRoute();
  const pathname = router.state.location.pathname;
  const api = useApi();
  const { theme, toggle: toggleTheme } = useTheme();
  const narrowNav = useNarrowNav();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    if (narrowNav) setSidebarOpen(false);
  }, [pathname, narrowNav]);

  const connections = useQuery({
    queryKey: ["connections"],
    queryFn: () => api.listConnections(),
    staleTime: 30_000,
  });
  const connCount = connections.data?.length ?? null;

  const email = auth.user?.profile.email ?? auth.devTenantId ?? "";
  const initials = email
    ? email.slice(0, 2).toUpperCase()
    : "?";

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: narrowNav ? "1fr" : "220px 1fr",
        height: "100dvh",
        position: "relative",
        zIndex: 1,
        fontSize: 13,
      }}
    >
      <a href="#main-content" className="skip-to-content">
        Skip to content
      </a>
      {narrowNav && sidebarOpen && (
        <button
          type="button"
          aria-label="Close navigation"
          onClick={() => setSidebarOpen(false)}
          style={{
            position: "fixed",
            inset: 0,
            zIndex: 38,
            border: "none",
            padding: 0,
            margin: 0,
            background: "rgba(10,10,10,0.35)",
            cursor: "pointer",
          }}
        />
      )}
      {/* Sidebar */}
      <aside
        id="app-sidebar"
        role="navigation"
        aria-label="Primary"
        style={{
          background: "var(--surface-2)",
          borderRight: narrowNav ? "none" : "1px solid var(--border)",
          display: "flex",
          flexDirection: "column",
          padding: "12px 10px",
          overflow: "hidden",
          ...(narrowNav
            ? {
                position: "fixed",
                left: 0,
                top: 0,
                bottom: 0,
                width: 220,
                zIndex: 40,
                transform: sidebarOpen ? "translateX(0)" : "translateX(-100%)",
                transition: "transform 0.22s ease, box-shadow 0.22s ease",
                boxShadow: sidebarOpen ? "var(--shadow-lg)" : "none",
              }
            : {}),
        }}
      >
        {/* Logo */}
        <div
          style={{
            padding: "6px 8px 12px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <Link to="/home" onClick={() => narrowNav && setSidebarOpen(false)} style={{ display: "inline-flex" }}>
            <HarnexLogo size={20} />
          </Link>
          <span
            className="badge badge-slate badge-mono"
            style={{ height: 18, fontSize: 10 }}
          >
            v0.4
          </span>
        </div>

        {/* Org switcher */}
        <button
          style={{
            display: "flex",
            alignItems: "center",
            gap: 8,
            padding: "8px 8px",
            border: "1px solid var(--border)",
            borderRadius: 6,
            background: "var(--surface)",
            marginBottom: 12,
            cursor: "pointer",
            textAlign: "left",
            width: "100%",
          }}
        >
          <span
            style={{
              width: 22,
              height: 22,
              borderRadius: 4,
              background: "var(--ink)",
              color: "#fff",
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 10,
              fontWeight: 700,
              flexShrink: 0,
            }}
          >
            {initials.slice(0, 1)}
          </span>
          <span
            style={{
              flex: 1,
              fontSize: 12.5,
              fontWeight: 500,
              overflow: "hidden",
              textOverflow: "ellipsis",
              whiteSpace: "nowrap",
            }}
          >
            {email.split("@")[0] ?? "workspace"}
          </span>
          <ChevronDown size={12} color="var(--muted)" />
        </button>

        {/* Nav */}
        <div style={{ display: "flex", flexDirection: "column", gap: 1 }}>
          {NAV.map((item) => {
            const Icon = item.icon;
            const active =
              item.to === "/connections"
                ? Boolean(matchRoute({ to: "/connections", fuzzy: true }))
                : Boolean(matchRoute({ to: item.to, fuzzy: false }));
            const isConnections = item.to === "/connections";
            return (
              <Link
                key={item.to}
                to={item.to}
                onClick={() => narrowNav && setSidebarOpen(false)}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 9,
                  padding: "6px 8px",
                  borderRadius: 5,
                  background: active ? "var(--surface)" : "transparent",
                  color: active ? "var(--ink)" : "var(--slate)",
                  fontSize: 12.5,
                  fontWeight: active ? 500 : 400,
                  cursor: "pointer",
                  textDecoration: "none",
                  boxShadow: active ? "var(--shadow-sm)" : "none",
                  border: active
                    ? "1px solid var(--border)"
                    : "1px solid transparent",
                  transition: "all 80ms ease",
                }}
              >
                <Icon
                  size={14}
                  style={{ color: active ? "var(--ink)" : "var(--muted)", flexShrink: 0 }}
                />
                <span style={{ flex: 1 }}>{item.label}</span>
                {isConnections && connCount !== null && (
                  <span
                    className="mono"
                    style={{ fontSize: 10.5, color: "var(--muted)" }}
                  >
                    {connCount}
                  </span>
                )}
              </Link>
            );
          })}
        </div>

        {/* Reference */}
        <div style={{ marginTop: 18, padding: "0 8px 6px" }} className="kicker">
          Reference
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 1 }}>
          <Link
            to="/style-guide"
            onClick={() => narrowNav && setSidebarOpen(false)}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 9,
              padding: "6px 8px",
              borderRadius: 5,
              background: pathname === "/style-guide" ? "var(--surface)" : "transparent",
              color: pathname === "/style-guide" ? "var(--ink)" : "var(--slate)",
              fontSize: 12.5,
              cursor: "pointer",
              textDecoration: "none",
              border: pathname === "/style-guide"
                ? "1px solid var(--border)"
                : "1px solid transparent",
              transition: "all 80ms ease",
            }}
          >
            <span style={{ display: "inline-flex", color: pathname === "/style-guide" ? "var(--ink)" : "var(--muted)" }}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M18 3a3 3 0 0 0-3 3v12a3 3 0 0 0 3 3 3 3 0 0 0 3-3 3 3 0 0 0-3-3H6a3 3 0 0 0-3 3 3 3 0 0 0 3 3 3 3 0 0 0 3-3V6a3 3 0 0 0-3-3 3 3 0 0 0-3 3 3 3 0 0 0 3 3h12a3 3 0 0 0 3-3 3 3 0 0 0-3-3z"/></svg>
            </span>
            <span>Style Guide</span>
          </Link>
        </div>

        {/* User profile */}
        <div
          style={{
            marginTop: "auto",
            borderTop: "1px solid var(--border)",
            paddingTop: 12,
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              padding: "6px 8px",
            }}
          >
            <span
              style={{
                width: 24,
                height: 24,
                borderRadius: 999,
                background: "linear-gradient(135deg, var(--ink), var(--slate))",
                color: "#fff",
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: 10,
                fontWeight: 600,
                flexShrink: 0,
              }}
            >
              {initials}
            </span>
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                lineHeight: 1.2,
                flex: 1,
                overflow: "hidden",
              }}
            >
              <span
                style={{
                  fontSize: 12,
                  fontWeight: 500,
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap",
                }}
              >
                {email.split("@")[0] || "dev user"}
              </span>
              <span
                style={{
                  fontSize: 10.5,
                  color: "var(--muted)",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap",
                }}
              >
                {email}
              </span>
            </div>
            <Link
              to="/settings"
              style={{
                background: "none",
                border: "none",
                padding: 4,
                cursor: "pointer",
                color: "var(--muted)",
                display: "flex",
                alignItems: "center",
                textDecoration: "none",
              }}
              title="Settings"
            >
              <Settings size={13} />
            </Link>
            <button
              onClick={() => void auth.signOut()}
              style={{
                background: "none",
                border: "none",
                padding: 4,
                cursor: "pointer",
                color: "var(--muted)",
                display: "flex",
                alignItems: "center",
              }}
              title="Sign out"
            >
              <LogOut size={13} />
            </button>
          </div>
        </div>
      </aside>

      {/* Main */}
      <div style={{ display: "flex", flexDirection: "column", overflow: "hidden" }}>
        {/* Topbar */}
        <header
          className="app-topbar"
          role="banner"
          style={{
            height: 44,
            borderBottom: "1px solid var(--border)",
            display: "flex",
            alignItems: "center",
            padding: "0 20px",
            gap: 12,
            background: "var(--bg)",
            flexShrink: 0,
          }}
        >
          {narrowNav && (
            <button
              type="button"
              className="btn btn-ghost btn-sm"
              style={{ width: 36, padding: 0, flexShrink: 0 }}
              onClick={() => setSidebarOpen((v) => !v)}
              aria-expanded={sidebarOpen}
              aria-controls="app-sidebar"
              aria-label={sidebarOpen ? "Close navigation menu" : "Open navigation menu"}
            >
              <Menu size={18} />
            </button>
          )}
          <h1
            className="app-topbar-title"
            style={{ fontSize: 14, fontWeight: 500, margin: 0, color: "var(--ink)" }}
          >
            {shellPageTitle(matchRoute)}
          </h1>
          <span className="app-topbar-actions" style={{ marginLeft: "auto" }}>
            <a
              href="https://docs.harnex.dev"
              target="_blank"
              rel="noopener noreferrer"
              className="btn btn-ghost btn-sm app-topbar-docs"
              style={{ gap: 5 }}
            >
              <BookOpen size={12} />
              Docs
            </a>
            <button
              className="btn btn-ghost btn-sm"
              style={{ width: 28, padding: 0 }}
              onClick={toggleTheme}
              title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
            >
              {theme === "dark" ? <Sun size={13} /> : <Moon size={13} />}
            </button>
            <button className="btn btn-ghost btn-sm" style={{ width: 28, padding: 0 }}>
              <Bell size={13} />
            </button>
            <span
              className="mono app-topbar-kbd"
              style={{
                fontSize: 11,
                color: "var(--muted)",
                border: "1px solid var(--border)",
                padding: "2px 6px",
                borderRadius: 4,
                background: "var(--surface)",
              }}
            >
              ⌘K
            </span>
          </span>
        </header>

        {/* Content */}
        <main id="main-content" style={{ flex: 1, overflow: "auto" }} tabIndex={-1}>
          <div className="app-content-pad">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
