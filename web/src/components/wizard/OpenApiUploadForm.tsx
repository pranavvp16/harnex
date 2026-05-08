import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect, useRef, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import {
  AuthConfigSection,
  authConfigSchema,
} from "@/components/wizard/AuthConfigSection";
import { FormActions, FormCard, FormField } from "@/components/wizard/BuiltinConnectorForm";
import { buildInput, useEmitGenericState } from "@/components/wizard/OpenApiUrlForm";
import type { WizardFormState } from "@/components/wizard/types";
import type { CreateConnectionInput } from "@/lib/api";

const schema = z
  .object({
    name: z.string().min(1, "Required"),
    base_url: z.string().url("Must be a URL").optional().or(z.literal("")),
  })
  .merge(authConfigSchema);
type Values = z.infer<typeof schema>;

interface Props {
  onSubmit?: (input: CreateConnectionInput, file?: File) => void;
  submitting: boolean;
  embedded?: boolean;
  onNameChange?: (name: string) => void;
  onStateChange?: (state: WizardFormState | null) => void;
}

export function OpenApiUploadForm({
  onSubmit,
  submitting,
  embedded,
  onNameChange,
  onStateChange,
}: Props) {
  const [file, setFile] = useState<File | null>(null);
  const fileRef = useRef<File | null>(null);
  const form = useForm<Values>({
    resolver: zodResolver(schema),
    defaultValues: { name: "", base_url: "", auth_flow: "none" },
  });
  const nameValue = form.watch("name");
  useEffect(() => { onNameChange?.(nameValue); }, [nameValue, onNameChange]);
  useEmitGenericState(form, "openapi_upload", onStateChange, fileRef);

  function setFileBoth(next: File | null) {
    fileRef.current = next;
    setFile(next);
    // Re-emit with the new file by triggering a watch tick.
    form.setValue("name", form.getValues("name"));
  }

  function handle(values: Values) {
    const input = buildInput(
      { ...values, spec_url: "" } as Values & { spec_url: string },
      "openapi_upload",
    );
    onSubmit?.(input, file ?? undefined);
  }

  return (
    <FormCard title="Upload an OpenAPI spec" hint="JSON or YAML, OpenAPI 3.x or Swagger 2.0">
      <FormField label="Connection name" htmlFor="up-name" error={form.formState.errors.name?.message}>
        <input className="input" id="up-name" {...form.register("name")} />
      </FormField>
      <FormField label="Spec file" htmlFor="up-spec_file">
        <input
          id="up-spec_file"
          type="file"
          className="input"
          accept=".json,.yaml,.yml,application/json,text/yaml"
          onChange={(e) => setFileBoth(e.target.files?.[0] ?? null)}
        />
      </FormField>
      <FormField label="Base URL override" htmlFor="up-base_url">
        <input className="input" id="up-base_url" {...form.register("base_url")} />
      </FormField>
      <AuthConfigSection form={form} />
      {!embedded && (
        <FormActions submitting={submitting} onSubmit={form.handleSubmit(handle)} disabled={!file} />
      )}
    </FormCard>
  );
}
