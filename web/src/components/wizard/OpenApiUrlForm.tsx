import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/Card";
import { Field } from "@/components/ui/Field";
import { Input } from "@/components/ui/Input";
import { AuthConfigSection, type AuthValues, authConfigSchema } from "@/components/wizard/AuthConfigSection";
import type { CreateConnectionInput } from "@/lib/api";

const schema = z
  .object({
    name: z.string().min(1, "Required"),
    spec_url: z.string().url("Must be a URL"),
    base_url: z.string().url("Must be a URL").optional().or(z.literal("")),
  })
  .merge(authConfigSchema);
type Values = z.infer<typeof schema>;

interface Props {
  onSubmit: (input: CreateConnectionInput) => void;
  submitting: boolean;
}

export function OpenApiUrlForm({ onSubmit, submitting }: Props) {
  const form = useForm<Values>({
    resolver: zodResolver(schema),
    defaultValues: { name: "", spec_url: "", base_url: "", auth_flow: "none" },
  });

  function handle(values: Values) {
    onSubmit(buildInput(values, "openapi_url"));
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Connect via OpenAPI URL</CardTitle>
      </CardHeader>
      <CardBody className="flex flex-col gap-4">
        <Field label="Connection name" htmlFor="name" error={form.formState.errors.name?.message}>
          <Input id="name" {...form.register("name")} />
        </Field>
        <Field
          label="OpenAPI / Swagger URL"
          htmlFor="spec_url"
          error={form.formState.errors.spec_url?.message}
          hint="JSON or YAML, OpenAPI 3.x or Swagger 2.0"
        >
          <Input
            id="spec_url"
            placeholder="https://example.com/openapi.json"
            {...form.register("spec_url")}
          />
        </Field>
        <Field
          label="Base URL override"
          htmlFor="base_url"
          hint="Optional; defaults to the spec's `servers[0].url`"
        >
          <Input id="base_url" {...form.register("base_url")} />
        </Field>
        <AuthConfigSection form={form} />
        <div className="flex justify-end">
          <Button onClick={form.handleSubmit(handle)} disabled={submitting}>
            {submitting ? "Creating…" : "Create connection"}
          </Button>
        </div>
      </CardBody>
    </Card>
  );
}

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
    spec_url: "spec_url" in values ? values.spec_url || null : null,
    auth_config,
    credentials,
  };
}
