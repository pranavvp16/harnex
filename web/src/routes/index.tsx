import { createFileRoute, redirect } from "@tanstack/react-router";

export const Route = createFileRoute("/")({
  beforeLoad: ({ context }) => {
    if (context.auth.status === "authenticated") {
      throw redirect({ to: "/dashboard" });
    }
    if (context.auth.status === "anonymous") {
      throw redirect({ to: "/home" });
    }
  },
  component: () => null,
});
