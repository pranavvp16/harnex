import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";
import { Github, Globe, Hammer, KeyRound, UploadCloud } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/Card";
import { BareUrlForm } from "@/components/wizard/BareUrlForm";
import { BuiltinConnectorForm } from "@/components/wizard/BuiltinConnectorForm";
import { OpenApiUploadForm } from "@/components/wizard/OpenApiUploadForm";
import { OpenApiUrlForm } from "@/components/wizard/OpenApiUrlForm";
import type { CreateConnectionInput } from "@/lib/api";
import { useApi } from "@/lib/useApi";

export type WizardChoice =
  | { kind: "builtin"; connectorKey: "github" | "jenkins" }
  | { kind: "openapi_url" }
  | { kind: "openapi_upload" }
  | { kind: "bare_url" };

interface Props {
  step: "choose" | "form";
  setStep: (s: "choose" | "form") => void;
}

export function ConnectionWizard({ step, setStep }: Props) {
  const [choice, setChoice] = useState<WizardChoice | null>(null);
  const navigate = useNavigate();
  const api = useApi();
  const qc = useQueryClient();

  const create = useMutation({
    mutationFn: (input: CreateConnectionInput) => api.createConnection(input),
    onSuccess: async (created) => {
      await qc.invalidateQueries({ queryKey: ["connections"] });
      navigate({ to: "/connections", search: { highlight: created.id } });
    },
  });

  if (step === "choose") {
    return (
      <ChoosePanel
        onPick={(c) => {
          setChoice(c);
          setStep("form");
        }}
      />
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <Button
        variant="ghost"
        size="sm"
        className="self-start"
        onClick={() => {
          setChoice(null);
          setStep("choose");
        }}
      >
        ← Back
      </Button>
      {choice?.kind === "builtin" && (
        <BuiltinConnectorForm
          connectorKey={choice.connectorKey}
          onSubmit={(payload) => create.mutate(payload)}
          submitting={create.isPending}
        />
      )}
      {choice?.kind === "openapi_url" && (
        <OpenApiUrlForm
          onSubmit={(payload) => create.mutate(payload)}
          submitting={create.isPending}
        />
      )}
      {choice?.kind === "openapi_upload" && (
        <OpenApiUploadForm
          onSubmit={(payload) => create.mutate(payload)}
          submitting={create.isPending}
        />
      )}
      {choice?.kind === "bare_url" && (
        <BareUrlForm
          onSubmit={(payload) => create.mutate(payload)}
          submitting={create.isPending}
        />
      )}
      {create.error && (
        <p className="text-sm text-red-600">Failed to create: {String(create.error)}</p>
      )}
    </div>
  );
}

function ChoosePanel({ onPick }: { onPick: (c: WizardChoice) => void }) {
  const tiles: {
    label: string;
    description: string;
    icon: React.ComponentType<{ className?: string }>;
    pick: WizardChoice;
  }[] = [
    {
      label: "GitHub",
      description: "OAuth or personal access token. Curated OpenAPI spec.",
      icon: Github,
      pick: { kind: "builtin", connectorKey: "github" },
    },
    {
      label: "Jenkins",
      description: "API token / basic auth. Bring your own spec.",
      icon: Hammer,
      pick: { kind: "builtin", connectorKey: "jenkins" },
    },
    {
      label: "OpenAPI URL",
      description: "Paste a link to a published OpenAPI 3 / Swagger 2 spec.",
      icon: Globe,
      pick: { kind: "openapi_url" },
    },
    {
      label: "Upload OpenAPI",
      description: "Upload a JSON or YAML spec file.",
      icon: UploadCloud,
      pick: { kind: "openapi_upload" },
    },
    {
      label: "Bare API URL",
      description: "Just a base URL + auth. Useful for internal services.",
      icon: KeyRound,
      pick: { kind: "bare_url" },
    },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>How do you want to connect?</CardTitle>
      </CardHeader>
      <CardBody className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
        {tiles.map((t) => (
          <button
            key={t.label}
            onClick={() => onPick(t.pick)}
            className="focus-ring flex flex-col items-start gap-2 rounded-lg border border-slate-200 bg-white p-4 text-left transition-colors hover:border-brand-500 hover:bg-brand-50/50"
          >
            <div className="flex items-center gap-2">
              <t.icon className="h-5 w-5 text-slate-700" />
              <span className="font-medium text-slate-900">{t.label}</span>
            </div>
            <p className="text-sm text-slate-600">{t.description}</p>
          </button>
        ))}
      </CardBody>
    </Card>
  );
}
