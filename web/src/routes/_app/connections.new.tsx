import { createFileRoute } from "@tanstack/react-router";

import { ConnectionWizard } from "@/components/wizard/ConnectionWizard";

export const Route = createFileRoute("/_app/connections/new")({
  component: NewConnection,
});

function NewConnection() {
  return <ConnectionWizard />;
}
