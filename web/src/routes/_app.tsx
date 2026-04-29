import { Link, Outlet, createFileRoute, redirect, useRouter } from "@tanstack/react-router";

import { Button } from "@/components/ui/Button";
import { useAuth } from "@/lib/auth";

export const Route = createFileRoute("/_app")({
  beforeLoad: ({ context, location }) => {
    if (context.auth.status === "loading") return;
    if (context.auth.status !== "authenticated") {
      throw redirect({
        to: "/login",
        search: { returnTo: location.pathname },
      });
    }
  },
  component: AppShell,
});

const NAV: { to: string; label: string }[] = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/connections", label: "Connections" },
  { to: "/api-keys", label: "API Keys" },
  { to: "/executions", label: "Executions" },
  { to: "/usage", label: "Usage" },
];

function AppShell() {
  const auth = useAuth();
  const router = useRouter();
  const pathname = router.state.location.pathname;

  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-6">
          <Link to="/dashboard" className="text-base font-semibold text-slate-900">
            Harnex
          </Link>
          <nav className="flex items-center gap-1">
            {NAV.map((item) => (
              <Link
                key={item.to}
                to={item.to}
                className={`rounded-md px-3 py-1.5 text-sm font-medium ${
                  pathname.startsWith(item.to)
                    ? "bg-slate-100 text-slate-900"
                    : "text-slate-600 hover:bg-slate-50"
                }`}
              >
                {item.label}
              </Link>
            ))}
          </nav>
          <div className="flex items-center gap-3">
            <span className="text-sm text-slate-600">{auth.user?.profile.email ?? ""}</span>
            <Button variant="ghost" size="sm" onClick={() => void auth.signOut()}>
              Sign out
            </Button>
          </div>
        </div>
      </header>
      <main className="mx-auto w-full max-w-6xl flex-1 px-6 py-8">
        <Outlet />
      </main>
    </div>
  );
}
