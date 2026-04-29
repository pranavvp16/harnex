import { Link, createFileRoute, redirect } from "@tanstack/react-router";

import { Button } from "@/components/ui/Button";

export const Route = createFileRoute("/")({
  beforeLoad: ({ context, location }) => {
    if (context.auth.status === "authenticated") {
      throw redirect({ to: "/dashboard" });
    }
    if (context.auth.status === "anonymous" && location.pathname === "/") {
      // fall through to landing
    }
  },
  component: Landing,
});

function Landing() {
  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col items-center justify-center gap-6 px-6">
      <h1 className="text-4xl font-semibold tracking-tight text-slate-900">Harnex</h1>
      <p className="max-w-xl text-center text-slate-600">
        Connect any HTTP API, search across endpoints semantically, and let your agents execute
        through one MCP server.
      </p>
      <Link to="/login">
        <Button size="lg">Sign in</Button>
      </Link>
    </main>
  );
}
