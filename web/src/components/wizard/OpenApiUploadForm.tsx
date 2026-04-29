import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/Card";
import { Field } from "@/components/ui/Field";
import { Input } from "@/components/ui/Input";
import { AuthConfigSection, authConfigSchema } from "@/components/wizard/AuthConfigSection";
import { buildInput } from "@/components/wizard/OpenApiUrlForm";
import type { CreateConnectionInput } from "@/lib/api";

const schema = z
  .object({
    name: z.string().min(1, "Required"),
    base_url: z.string().url("Must be a URL").optional().or(z.literal("")),
  })
  .merge(authConfigSchema);
type Values = z.infer<typeof schema>;

interface Props {
  onSubmit: (input: CreateConnectionInput, file?: File) => void;
  submitting: boolean;
}

export function OpenApiUploadForm({ onSubmit, submitting }: Props) {
  const [file, setFile] = useState<File | null>(null);
  const form = useForm<Values>({
    resolver: zodResolver(schema),
    defaultValues: { name: "", base_url: "", auth_flow: "none" },
  });

  function handle(values: Values) {
    const input = buildInput(
      { ...values, spec_url: "" } as Values & { spec_url: string },
      "openapi_upload",
    );
    onSubmit(input, file ?? undefined);
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Upload an OpenAPI spec</CardTitle>
      </CardHeader>
      <CardBody className="flex flex-col gap-4">
        <Field label="Connection name" htmlFor="name" error={form.formState.errors.name?.message}>
          <Input id="name" {...form.register("name")} />
        </Field>
        <Field
          label="Spec file"
          htmlFor="spec_file"
          hint="JSON or YAML, OpenAPI 3.x or Swagger 2.0"
        >
          <Input
            id="spec_file"
            type="file"
            accept=".json,.yaml,.yml,application/json,text/yaml"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
        </Field>
        <Field label="Base URL override" htmlFor="base_url">
          <Input id="base_url" {...form.register("base_url")} />
        </Field>
        <AuthConfigSection form={form} />
        <div className="flex justify-end">
          <Button onClick={form.handleSubmit(handle)} disabled={submitting || !file}>
            {submitting ? "Creating…" : "Create connection"}
          </Button>
        </div>
      </CardBody>
    </Card>
  );
}
