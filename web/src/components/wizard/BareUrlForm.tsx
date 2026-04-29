import { zodResolver } from "@hookform/resolvers/zod";
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
    base_url: z.string().url("Must be a URL"),
  })
  .merge(authConfigSchema);
type Values = z.infer<typeof schema>;

interface Props {
  onSubmit: (input: CreateConnectionInput) => void;
  submitting: boolean;
}

export function BareUrlForm({ onSubmit, submitting }: Props) {
  const form = useForm<Values>({
    resolver: zodResolver(schema),
    defaultValues: { name: "", base_url: "", auth_flow: "none" },
  });

  function handle(values: Values) {
    onSubmit(
      buildInput({ ...values, spec_url: "" } as Values & { spec_url: string }, "bare_url"),
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Connect a bare API URL</CardTitle>
      </CardHeader>
      <CardBody className="flex flex-col gap-4">
        <p className="text-sm text-slate-600">
          Without a spec, agents must supply method/path/body explicitly. You can attach an
          OpenAPI spec later to make the connection searchable.
        </p>
        <Field label="Connection name" htmlFor="name" error={form.formState.errors.name?.message}>
          <Input id="name" {...form.register("name")} />
        </Field>
        <Field
          label="Base URL"
          htmlFor="base_url"
          error={form.formState.errors.base_url?.message}
        >
          <Input id="base_url" placeholder="https://api.example.com" {...form.register("base_url")} />
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
