import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/Card";
import { Field } from "@/components/ui/Field";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import type { AuthFlow, CreateConnectionInput } from "@/lib/api";

interface Props {
  connectorKey: "github" | "jenkins";
  onSubmit: (input: CreateConnectionInput) => void;
  submitting: boolean;
}

const githubSchema = z.object({
  name: z.string().min(1, "Required"),
  auth_flow: z.enum(["bearer", "oauth_authcode"]),
  token: z.string().optional(),
});
type GithubValues = z.infer<typeof githubSchema>;

const jenkinsSchema = z.object({
  name: z.string().min(1, "Required"),
  base_url: z.string().url("Must be a URL"),
  auth_flow: z.enum(["basic", "bearer", "api_key_header"]),
  username: z.string().optional(),
  token: z.string().optional(),
});
type JenkinsValues = z.infer<typeof jenkinsSchema>;

export function BuiltinConnectorForm({ connectorKey, onSubmit, submitting }: Props) {
  if (connectorKey === "github") {
    return <GithubForm onSubmit={onSubmit} submitting={submitting} />;
  }
  return <JenkinsForm onSubmit={onSubmit} submitting={submitting} />;
}

function GithubForm({
  onSubmit,
  submitting,
}: {
  onSubmit: (input: CreateConnectionInput) => void;
  submitting: boolean;
}) {
  const form = useForm<GithubValues>({
    resolver: zodResolver(githubSchema),
    defaultValues: { name: "github", auth_flow: "bearer", token: "" },
  });
  const flow = form.watch("auth_flow");

  function handle(values: GithubValues) {
    const input: CreateConnectionInput = {
      name: values.name,
      mode: "builtin",
      connector_key: "github",
      auth_flow: values.auth_flow as AuthFlow,
      auth_config: {},
      credentials: values.auth_flow === "bearer" && values.token ? { token: values.token } : {},
    };
    onSubmit(input);
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Connect GitHub</CardTitle>
      </CardHeader>
      <CardBody className="flex flex-col gap-4">
        <Field label="Connection name" htmlFor="name">
          <Input id="name" {...form.register("name")} />
        </Field>
        <Field label="Auth method" htmlFor="auth_flow">
          <Select id="auth_flow" {...form.register("auth_flow")}>
            <option value="bearer">Personal access token</option>
            <option value="oauth_authcode">OAuth (sign in with GitHub)</option>
          </Select>
        </Field>
        {flow === "bearer" && (
          <Field
            label="Personal access token"
            htmlFor="token"
            hint="Sent only to Harnex; stored encrypted in Infisical, never in the browser."
            error={form.formState.errors.token?.message}
          >
            <Input id="token" type="password" autoComplete="off" {...form.register("token")} />
          </Field>
        )}
        {flow === "oauth_authcode" && (
          <p className="text-sm text-slate-600">
            We&apos;ll redirect you to GitHub to authorize after creating the connection.
          </p>
        )}
        <div className="flex justify-end">
          <Button onClick={form.handleSubmit(handle)} disabled={submitting}>
            {submitting ? "Creating…" : "Create connection"}
          </Button>
        </div>
      </CardBody>
    </Card>
  );
}

function JenkinsForm({
  onSubmit,
  submitting,
}: {
  onSubmit: (input: CreateConnectionInput) => void;
  submitting: boolean;
}) {
  const form = useForm<JenkinsValues>({
    resolver: zodResolver(jenkinsSchema),
    defaultValues: { name: "jenkins", auth_flow: "basic", base_url: "" },
  });
  const flow = form.watch("auth_flow");

  function handle(values: JenkinsValues) {
    const credentials: Record<string, string> = {};
    if (values.auth_flow === "basic") {
      if (values.username) credentials.username = values.username;
      if (values.token) credentials.password = values.token;
    } else if (values.auth_flow === "bearer" && values.token) {
      credentials.token = values.token;
    } else if (values.auth_flow === "api_key_header" && values.token) {
      credentials.api_key = values.token;
    }
    onSubmit({
      name: values.name,
      mode: "builtin",
      connector_key: "jenkins",
      base_url: values.base_url,
      auth_flow: values.auth_flow as AuthFlow,
      auth_config:
        values.auth_flow === "api_key_header" ? { header_name: "Authorization" } : {},
      credentials,
    });
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Connect Jenkins</CardTitle>
      </CardHeader>
      <CardBody className="flex flex-col gap-4">
        <Field label="Connection name" htmlFor="name">
          <Input id="name" {...form.register("name")} />
        </Field>
        <Field label="Base URL" htmlFor="base_url" error={form.formState.errors.base_url?.message}>
          <Input id="base_url" placeholder="https://jenkins.internal/" {...form.register("base_url")} />
        </Field>
        <Field label="Auth method" htmlFor="auth_flow">
          <Select id="auth_flow" {...form.register("auth_flow")}>
            <option value="basic">Username + API token (basic)</option>
            <option value="bearer">Bearer token</option>
            <option value="api_key_header">Custom header</option>
          </Select>
        </Field>
        {flow === "basic" && (
          <>
            <Field label="Username" htmlFor="username">
              <Input id="username" {...form.register("username")} />
            </Field>
            <Field label="API token" htmlFor="token">
              <Input id="token" type="password" autoComplete="off" {...form.register("token")} />
            </Field>
          </>
        )}
        {flow !== "basic" && (
          <Field label="Token" htmlFor="token">
            <Input id="token" type="password" autoComplete="off" {...form.register("token")} />
          </Field>
        )}
        <div className="flex justify-end">
          <Button onClick={form.handleSubmit(handle)} disabled={submitting}>
            {submitting ? "Creating…" : "Create connection"}
          </Button>
        </div>
      </CardBody>
    </Card>
  );
}
