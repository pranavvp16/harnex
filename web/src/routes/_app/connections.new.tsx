import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";

import { ConnectionWizard } from "@/components/wizard/ConnectionWizard";

export const Route = createFileRoute("/_app/connections/new")({
  component: NewConnection,
});

function NewConnection() {
  const [step, setStep] = useState<"choose" | "form">("choose");
  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-semibold text-slate-900">Connect an API</h1>
      <ConnectionWizard step={step} setStep={setStep} />
    </div>
  );
}
