import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect } from "react";
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
    base_url: z.string().url("Must be a URL"),
  })
  .merge(authConfigSchema);
type Values = z.infer<typeof schema>;

interface Props {
  onSubmit?: (input: CreateConnectionInput) => void;
  submitting: boolean;
  embedded?: boolean;
  onNameChange?: (name: string) => void;
  onStateChange?: (state: WizardFormState | null) => void;
}

export function BareUrlForm({
  onSubmit,
  submitting,
  embedded,
  onNameChange,
  onStateChange,
}: Props) {
  const form = useForm<Values>({
    resolver: zodResolver(schema),
    defaultValues: { name: "", base_url: "", auth_flow: "none" },
  });
  const nameValue = form.watch("name");
  useEffect(() => { onNameChange?.(nameValue); }, [nameValue, onNameChange]);
  useEmitGenericState(form, "bare_url", onStateChange);

  function handle(values: Values) {
    onSubmit?.(
      buildInput({ ...values, spec_url: "" } as Values & { spec_url: string }, "bare_url"),
    );
  }

  return (
    <FormCard title="Connect a bare API URL" hint="Without a spec, agents must supply method/path/body explicitly.">
      <FormField label="Connection name" htmlFor="br-name" error={form.formState.errors.name?.message}>
        <input className="input" id="br-name" {...form.register("name")} />
      </FormField>
      <FormField label="Base URL" htmlFor="br-base_url" error={form.formState.errors.base_url?.message}>
        <input className="input" id="br-base_url" placeholder="https://api.example.com" {...form.register("base_url")} />
      </FormField>
      <AuthConfigSection form={form} />
      {!embedded && <FormActions submitting={submitting} onSubmit={form.handleSubmit(handle)} />}
    </FormCard>
  );
}
