import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect } from "react";
import { useForm, type UseFormReturn } from "react-hook-form";
import { z } from "zod";

import {
  AuthConfigSection,
  authConfigSchema,
  type AuthValues,
} from "@/components/wizard/AuthConfigSection";
import { FormActions, FormCard, FormField } from "@/components/wizard/BuiltinConnectorForm";
import { authMethodLabel, maskSecret, type WizardFormState } from "@/components/wizard/types";
import type { CreateConnectionInput } from "@/lib/api";

const schema = z
  .object({
    name: z.string().min(1, "Required"),
    spec_url: z.string().url("Must be a valid URL"),
    base_url: z.string().url("Must be a valid URL").optional().or(z.literal("")),
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

export function OpenApiUrlForm({
  onSubmit,
  submitting,
  embedded,
  onNameChange,
  onStateChange,
}: Props) {
  const form = useForm<Values>({
    resolver: zodResolver(schema),
    defaultValues: { name: "", spec_url: "", base_url: "", auth_flow: "none" },
  });
  const nameValue = form.watch("name");
  useEffect(() => { onNameChange?.(nameValue); }, [nameValue, onNameChange]);
  useEmitGenericState(form, "openapi_url", onStateChange);
  const errors = form.formState.errors;

  function handle(values: Values) {
    onSubmit?.(buildInput(values, "openapi_url"));
  }

  return (
    <FormCard
      title="Connect via OpenAPI URL"
      hint="Harnex fetches and indexes the spec automatically."
    >
      <FormField label="Connection name" htmlFor="ou-name" error={errors.name?.message}>
        <input className="input" id="ou-name" {...form.register("name")} />
      </FormField>

      <FormField
        label="OpenAPI / Swagger URL"
        htmlFor="ou-spec_url"
        hint="JSON or YAML — OpenAPI 3.x or Swagger 2.0"
        error={errors.spec_url?.message}
      >
        <input
          className="input"
          id="ou-spec_url"
          placeholder="https://example.com/openapi.json"
          {...form.register("spec_url")}
        />
      </FormField>

      <FormField
        label="Base URL override"
        htmlFor="ou-base_url"
        hint="Optional — defaults to the spec's servers[0].url"
        error={errors.base_url?.message}
      >
        <input className="input" id="ou-base_url" placeholder="https://api.example.com" {...form.register("base_url")} />
      </FormField>

      <AuthConfigSection form={form} />

      {!embedded && (
        <FormActions submitting={submitting} onSubmit={form.handleSubmit(handle)} />
      )}
    </FormCard>
  );
}

// Shared builder used by OpenApiUrlForm and OpenApiUploadForm
export function buildInput(
  values: Values & AuthValues,
  mode: "openapi_url" | "openapi_upload" | "bare_url",
): CreateConnectionInput {
  const auth_config: Record<string, unknown> = {};
  const credentials: Record<string, string> = {};

  switch (values.auth_flow) {
    case "api_key_header":
      auth_config.header_name = values.header_name || "X-API-Key";
      if (values.prefix) auth_config.prefix = values.prefix;
      if (values.api_key) credentials.api_key = values.api_key;
      break;
    case "api_key_query":
      auth_config.query_name = values.query_name || "api_key";
      if (values.api_key) credentials.api_key = values.api_key;
      break;
    case "bearer":
      if (values.token) credentials.token = values.token;
      break;
    case "basic":
      if (values.username) credentials.username = values.username;
      if (values.password) credentials.password = values.password;
      break;
    default:
      break;
  }

  return {
    name: values.name,
    mode,
    auth_flow: values.auth_flow,
    base_url: values.base_url || null,
    spec_url: "spec_url" in values ? (values.spec_url as string) || null : null,
    auth_config,
    credentials,
  };
}

/** Build the wizard summary for any of the openapi/bare-url forms. */
export function buildGenericSummary(
  values: AuthValues & { name?: string; base_url?: string; spec_url?: string },
  mode: "openapi_url" | "openapi_upload" | "bare_url",
): { valid: boolean; summary: WizardFormState["summary"] } {
  const isHttpUrl = (v: string | undefined | null) => !!v && /^https?:\/\//.test(v);
  let valid = Boolean(values.name?.trim());
  if (mode === "openapi_url") valid = valid && isHttpUrl(values.spec_url);
  if (mode === "bare_url") valid = valid && isHttpUrl(values.base_url);

  let secretSummary: string | null;
  switch (values.auth_flow) {
    case "bearer":
      secretSummary = maskSecret(values.token);
      valid = valid && Boolean(values.token?.trim());
      break;
    case "basic":
      secretSummary = values.username
        ? `${values.username} · ${maskSecret(values.password) ?? "(no password)"}`
        : null;
      valid = valid && Boolean(values.username?.trim() && values.password?.trim());
      break;
    case "api_key_header":
    case "api_key_query":
      secretSummary = maskSecret(values.api_key);
      valid = valid && Boolean(values.api_key?.trim());
      break;
    case "none":
      secretSummary = null;
      break;
    default:
      secretSummary = null;
      break;
  }

  return {
    valid,
    summary: {
      authMethodLabel: authMethodLabel(values.auth_flow),
      secretSummary,
      isOAuth:
        values.auth_flow === "oauth_authcode" || values.auth_flow === "oauth_clientcred",
      oauthProvider: null,
    },
  };
}

export function useEmitGenericState<T extends AuthValues & { name?: string; base_url?: string; spec_url?: string }>(
  form: UseFormReturn<T>,
  mode: "openapi_url" | "openapi_upload" | "bare_url",
  onStateChange: ((state: WizardFormState | null) => void) | undefined,
  fileRef?: { current: File | null },
): void {
  useEffect(() => {
    if (!onStateChange) return;
    const emit = (values: T) => {
      const { valid, summary } = buildGenericSummary(values, mode);
      const padded = { spec_url: "", base_url: "", ...values } as unknown as Values &
        AuthValues;
      onStateChange({
        payload: buildInput(padded, mode),
        file: fileRef ? fileRef.current : null,
        valid: valid && (mode !== "openapi_upload" || (fileRef ? !!fileRef.current : true)),
        summary,
      });
    };
    emit(form.getValues() as T);
    const sub = form.watch((values) => emit(values as T));
    return () => sub.unsubscribe();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [form, onStateChange, mode, fileRef]);
}
