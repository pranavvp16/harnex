import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect, type ReactNode } from "react";
import { useForm, type UseFormReturn } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/Button";
import { Field } from "@/components/ui/Field";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { OAuthConsent } from "@/components/wizard/OAuthConsent";
import { maskSecret, type WizardFormState } from "@/components/wizard/types";
import type { AuthFlow, CreateConnectionInput } from "@/lib/api";

export type BuiltinConnectorKey =
  | "github"
  | "jenkins"
  | "gitlab"
  | "jira"
  | "kubernetes"
  | "linear"
  | "slack";

interface Props {
  connectorKey: BuiltinConnectorKey;
  onSubmit?: (input: CreateConnectionInput) => void;
  submitting: boolean;
  embedded?: boolean;
  onNameChange?: (name: string) => void;
  onStateChange?: (state: WizardFormState | null) => void;
}

type SubFormProps = Omit<Props, "connectorKey">;

/** Watch every field on the form and re-emit the lifted wizard state. */
function useEmitState<T extends Record<string, unknown>>(
  form: UseFormReturn<T>,
  onStateChange: ((state: WizardFormState | null) => void) | undefined,
  build: (values: T, valid: boolean) => WizardFormState,
): void {
  useEffect(() => {
    if (!onStateChange) return;
    onStateChange(build(form.getValues(), false));
    const sub = form.watch((values) => {
      onStateChange(build(values as T, false));
    });
    return () => sub.unsubscribe();
  }, [build, form, onStateChange]);
}

function FormSection({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <div style={{ paddingBottom: 12, borderBottom: "1px solid var(--border)" }}>
        <h2 style={{ fontSize: 15, fontWeight: 600, color: "var(--ink)", margin: 0 }}>{title}</h2>
      </div>
      <div className="flex flex-col gap-4">{children}</div>
    </section>
  );
}

// ── GitHub ────────────────────────────────────────────────────────────────────

const githubSchema = z.object({
  name: z.string().min(1, "Required"),
  auth_flow: z.enum(["bearer", "oauth_authcode"]),
  token: z.string().optional(),
});
type GithubValues = z.infer<typeof githubSchema>;

function buildGithubState(values: GithubValues): WizardFormState {
  const credentials: Record<string, string> = {};
  if (values.auth_flow === "bearer" && values.token) {
    credentials.token = values.token;
  }
  return {
    payload: {
      name: values.name,
      mode: "builtin",
      connector_key: "github",
      auth_flow: values.auth_flow as AuthFlow,
      auth_config: {},
      credentials,
    },
    valid:
      Boolean(values.name?.trim()) &&
      (values.auth_flow !== "bearer" || Boolean(values.token?.trim())),
    summary: {
      authMethodLabel:
        values.auth_flow === "bearer" ? "Personal access token" : "OAuth (sign in with GitHub)",
      secretSummary:
        values.auth_flow === "bearer" ? maskSecret(values.token) ?? "(not set)" : null,
      isOAuth: values.auth_flow === "oauth_authcode",
      oauthProvider: values.auth_flow === "oauth_authcode" ? "GitHub" : null,
    },
  };
}

function GithubForm({ onSubmit, submitting, embedded, onNameChange, onStateChange }: SubFormProps) {
  const form = useForm<GithubValues>({
    resolver: zodResolver(githubSchema),
    defaultValues: { name: "github", auth_flow: "bearer", token: "" },
  });
  const flow = form.watch("auth_flow");
  const nameValue = form.watch("name");
  useEffect(() => { onNameChange?.(nameValue); }, [nameValue, onNameChange]);
  useEmitState(form, onStateChange, buildGithubState);

  function handle(values: GithubValues) {
    onSubmit?.(buildGithubState(values).payload);
  }

  return (
    <FormSection title="Connect GitHub">
      <Field label="Connection name" htmlFor="name">
        <Input id="name" {...form.register("name")} />
      </Field>
      <Field label="Auth method" htmlFor="auth_flow">
        <Select id="auth_flow" {...form.register("auth_flow")}>
          <option value="bearer">Personal access token</option>
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
        <OAuthConsent provider="GitHub" />
      )}
      {!embedded && (
        <div className="flex justify-end">
          <Button onClick={form.handleSubmit(handle)} disabled={submitting}>
            {submitting ? "Creating…" : "Create connection"}
          </Button>
        </div>
      )}
    </FormSection>
  );
}

// ── Jenkins ───────────────────────────────────────────────────────────────────

const jenkinsSchema = z.object({
  name: z.string().min(1, "Required"),
  base_url: z.string().url("Must be a URL"),
  spec_url: z.string().url("Must be a valid URL"),
  auth_flow: z.enum(["basic", "bearer", "api_key_header"]),
  username: z.string().optional(),
  token: z.string().optional(),
});
type JenkinsValues = z.infer<typeof jenkinsSchema>;

function buildJenkinsState(values: JenkinsValues): WizardFormState {
  const credentials: Record<string, string> = {};
  if (values.auth_flow === "basic") {
    if (values.username) credentials.username = values.username;
    if (values.token) credentials.password = values.token;
  } else if (values.auth_flow === "bearer" && values.token) {
    credentials.token = values.token;
  } else if (values.auth_flow === "api_key_header" && values.token) {
    credentials.api_key = values.token;
  }
  const isUrl = /^https?:\/\//.test(values.base_url ?? "");
  const isSpecUrl = /^https?:\/\//.test(values.spec_url ?? "");
  const valid = Boolean(values.name?.trim() && isUrl && isSpecUrl);
  let secretSummary: string | null = null;
  if (values.auth_flow === "basic") {
    secretSummary = values.username
      ? `${values.username} · ${maskSecret(values.token) ?? "(no token)"}`
      : null;
  } else {
    secretSummary = maskSecret(values.token);
  }
  return {
    payload: {
      name: values.name,
      mode: "builtin",
      connector_key: "jenkins",
      base_url: values.base_url,
      spec_url: values.spec_url,
      auth_flow: values.auth_flow as AuthFlow,
      auth_config:
        values.auth_flow === "api_key_header" ? { header_name: "Authorization" } : {},
      credentials,
    },
    valid,
    summary: {
      authMethodLabel:
        values.auth_flow === "basic"
          ? "Username + API token (basic)"
          : values.auth_flow === "bearer"
            ? "Bearer token"
            : "Custom header",
      secretSummary,
      isOAuth: false,
      oauthProvider: null,
    },
  };
}

function JenkinsForm({ onSubmit, submitting, embedded, onNameChange, onStateChange }: SubFormProps) {
  const form = useForm<JenkinsValues>({
    resolver: zodResolver(jenkinsSchema),
    defaultValues: { name: "jenkins", auth_flow: "basic", base_url: "" },
  });
  const flow = form.watch("auth_flow");
  const nameValue = form.watch("name");
  useEffect(() => { onNameChange?.(nameValue); }, [nameValue, onNameChange]);
  useEmitState(form, onStateChange, buildJenkinsState);

  function handle(values: JenkinsValues) {
    onSubmit?.(buildJenkinsState(values).payload);
  }

  return (
    <FormSection title="Connect Jenkins">
      <Field label="Connection name" htmlFor="name">
        <Input id="name" {...form.register("name")} />
      </Field>
      <Field label="Base URL" htmlFor="base_url" error={form.formState.errors.base_url?.message}>
        <Input id="base_url" placeholder="https://jenkins.internal/" {...form.register("base_url")} />
      </Field>
      <Field
        label="Spec URL"
        htmlFor="spec_url"
        hint="Required — URL to a Jenkins OpenAPI spec (e.g. /swagger.json via the Swagger plugin). If your cluster doesn't expose one, use the OpenAPI Upload mode instead."
        error={form.formState.errors.spec_url?.message}
      >
        <Input id="spec_url" placeholder="https://jenkins.internal/swagger.json" {...form.register("spec_url")} />
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
      {!embedded && (
        <div className="flex justify-end">
          <Button onClick={form.handleSubmit(handle)} disabled={submitting}>
            {submitting ? "Creating…" : "Create connection"}
          </Button>
        </div>
      )}
    </FormSection>
  );
}

// ── GitLab ────────────────────────────────────────────────────────────────────

const gitlabSchema = z.object({
  name: z.string().min(1, "Required"),
  base_url: z.string().url("Must be a valid URL").optional().or(z.literal("")),
  auth_flow: z.enum(["bearer", "oauth_authcode", "api_key_header"]),
  token: z.string().optional(),
});
type GitLabValues = z.infer<typeof gitlabSchema>;

function buildGitLabState(values: GitLabValues): WizardFormState {
  const auth_config: Record<string, unknown> = {};
  const credentials: Record<string, string> = {};
  if (values.auth_flow === "api_key_header") {
    auth_config.header_name = "PRIVATE-TOKEN";
    if (values.token) credentials.api_key = values.token;
  } else if (values.auth_flow === "bearer" && values.token) {
    credentials.token = values.token;
  }
  const valid =
    Boolean(values.name?.trim()) &&
    (values.auth_flow === "oauth_authcode" || Boolean(values.token?.trim()));
  return {
    payload: {
      name: values.name,
      mode: "builtin",
      connector_key: "gitlab",
      base_url: values.base_url || null,
      auth_flow: values.auth_flow as AuthFlow,
      auth_config,
      credentials,
    },
    valid,
    summary: {
      authMethodLabel:
        values.auth_flow === "bearer"
          ? "Personal access token"
          : values.auth_flow === "api_key_header"
            ? "PRIVATE-TOKEN header"
            : "OAuth (sign in with GitLab)",
      secretSummary:
        values.auth_flow === "oauth_authcode" ? null : maskSecret(values.token) ?? "(not set)",
      isOAuth: values.auth_flow === "oauth_authcode",
      oauthProvider: values.auth_flow === "oauth_authcode" ? "GitLab" : null,
    },
  };
}

function GitLabForm({ onSubmit, submitting, embedded, onNameChange, onStateChange }: SubFormProps) {
  const form = useForm<GitLabValues>({
    resolver: zodResolver(gitlabSchema),
    defaultValues: { name: "gitlab", auth_flow: "bearer", token: "" },
  });
  const flow = form.watch("auth_flow");
  const nameValue = form.watch("name");
  useEffect(() => { onNameChange?.(nameValue); }, [nameValue, onNameChange]);
  useEmitState(form, onStateChange, buildGitLabState);

  function handle(values: GitLabValues) {
    onSubmit?.(buildGitLabState(values).payload);
  }

  return (
    <FormSection title="Connect GitLab">
      <Field label="Connection name" htmlFor="name">
        <Input id="name" {...form.register("name")} />
      </Field>
      <Field label="Base URL" htmlFor="base_url" hint="Optional — defaults to https://gitlab.com" error={form.formState.errors.base_url?.message}>
        <Input id="base_url" placeholder="https://gitlab.com" {...form.register("base_url")} />
      </Field>
      <Field label="Auth method" htmlFor="auth_flow">
        <Select id="auth_flow" {...form.register("auth_flow")}>
          <option value="bearer">Personal access token</option>
          <option value="api_key_header">PRIVATE-TOKEN header</option>
        </Select>
      </Field>
      {(flow === "bearer" || flow === "api_key_header") && (
        <Field
          label={flow === "bearer" ? "Personal access token" : "PRIVATE-TOKEN"}
          htmlFor="token"
          hint="Sent only to Harnex; stored encrypted in Infisical, never in the browser."
          error={form.formState.errors.token?.message}
        >
          <Input id="token" type="password" autoComplete="off" {...form.register("token")} />
        </Field>
      )}
      {flow === "oauth_authcode" && (
        <OAuthConsent provider="GitLab" />
      )}
      {!embedded && (
        <div className="flex justify-end">
          <Button onClick={form.handleSubmit(handle)} disabled={submitting}>
            {submitting ? "Creating…" : "Create connection"}
          </Button>
        </div>
      )}
    </FormSection>
  );
}

// ── Jira ──────────────────────────────────────────────────────────────────────

const jiraSchema = z.object({
  name: z.string().min(1, "Required"),
  base_url: z.string().url("Must be a valid URL"),
  auth_flow: z.enum(["basic", "bearer", "oauth_authcode"]),
  username: z.string().optional(),
  token: z.string().optional(),
});
type JiraValues = z.infer<typeof jiraSchema>;

function buildJiraState(values: JiraValues): WizardFormState {
  const credentials: Record<string, string> = {};
  if (values.auth_flow === "basic") {
    if (values.username) credentials.username = values.username;
    if (values.token) credentials.password = values.token;
  } else if (values.auth_flow === "bearer" && values.token) {
    credentials.token = values.token;
  }
  const isUrl = /^https?:\/\//.test(values.base_url ?? "");
  let valid = Boolean(values.name?.trim() && isUrl);
  if (values.auth_flow === "basic") {
    valid = valid && Boolean(values.username?.trim() && values.token?.trim());
  } else if (values.auth_flow === "bearer") {
    valid = valid && Boolean(values.token?.trim());
  }
  let secretSummary: string | null;
  if (values.auth_flow === "basic") {
    secretSummary = values.username
      ? `${values.username} · ${maskSecret(values.token) ?? "(no token)"}`
      : null;
  } else if (values.auth_flow === "bearer") {
    secretSummary = maskSecret(values.token);
  } else {
    secretSummary = null;
  }
  return {
    payload: {
      name: values.name,
      mode: "builtin",
      connector_key: "jira",
      base_url: values.base_url,
      auth_flow: values.auth_flow as AuthFlow,
      auth_config: {},
      credentials,
    },
    valid,
    summary: {
      authMethodLabel:
        values.auth_flow === "basic"
          ? "Email + API token (basic)"
          : values.auth_flow === "bearer"
            ? "Bearer token"
            : "OAuth 2.0 (3LO)",
      secretSummary,
      isOAuth: values.auth_flow === "oauth_authcode",
      oauthProvider: values.auth_flow === "oauth_authcode" ? "Atlassian" : null,
    },
  };
}

function JiraForm({ onSubmit, submitting, embedded, onNameChange, onStateChange }: SubFormProps) {
  const form = useForm<JiraValues>({
    resolver: zodResolver(jiraSchema),
    defaultValues: { name: "jira", auth_flow: "basic", base_url: "" },
  });
  const flow = form.watch("auth_flow");
  const nameValue = form.watch("name");
  useEffect(() => { onNameChange?.(nameValue); }, [nameValue, onNameChange]);
  useEmitState(form, onStateChange, buildJiraState);

  function handle(values: JiraValues) {
    onSubmit?.(buildJiraState(values).payload);
  }

  return (
    <FormSection title="Connect Jira">
      <Field label="Connection name" htmlFor="name">
        <Input id="name" {...form.register("name")} />
      </Field>
      <Field label="Base URL" htmlFor="base_url" error={form.formState.errors.base_url?.message}>
        <Input id="base_url" placeholder="https://your-org.atlassian.net" {...form.register("base_url")} />
      </Field>
      <Field label="Auth method" htmlFor="auth_flow">
        <Select id="auth_flow" {...form.register("auth_flow")}>
          <option value="basic">Email + API token (basic)</option>
          <option value="bearer">Bearer token</option>
        </Select>
      </Field>
      {flow === "basic" && (
        <>
          <Field label="Email" htmlFor="username">
            <Input id="username" {...form.register("username")} />
          </Field>
          <Field label="API token" htmlFor="token">
            <Input id="token" type="password" autoComplete="off" {...form.register("token")} />
          </Field>
        </>
      )}
      {flow === "bearer" && (
        <Field label="Bearer token" htmlFor="token">
          <Input id="token" type="password" autoComplete="off" {...form.register("token")} />
        </Field>
      )}
      {flow === "oauth_authcode" && (
        <OAuthConsent provider="Atlassian" />
      )}
      {!embedded && (
        <div className="flex justify-end">
          <Button onClick={form.handleSubmit(handle)} disabled={submitting}>
            {submitting ? "Creating…" : "Create connection"}
          </Button>
        </div>
      )}
    </FormSection>
  );
}

// ── Kubernetes ────────────────────────────────────────────────────────────────

const kubernetesSchema = z.object({
  name: z.string().min(1, "Required"),
  base_url: z.string().url("Must be a valid URL"),
  spec_url: z.string().url("Must be a valid URL").optional().or(z.literal("")),
  auth_flow: z.enum(["bearer", "basic"]),
  username: z.string().optional(),
  token: z.string().optional(),
});
type KubernetesValues = z.infer<typeof kubernetesSchema>;

function buildKubernetesState(values: KubernetesValues): WizardFormState {
  const credentials: Record<string, string> = {};
  if (values.auth_flow === "basic") {
    if (values.username) credentials.username = values.username;
    if (values.token) credentials.password = values.token;
  } else if (values.auth_flow === "bearer" && values.token) {
    credentials.token = values.token;
  }
  const isUrl = /^https?:\/\//.test(values.base_url ?? "");
  let valid = Boolean(values.name?.trim() && isUrl);
  if (values.auth_flow === "basic") {
    valid = valid && Boolean(values.username?.trim() && values.token?.trim());
  } else {
    valid = valid && Boolean(values.token?.trim());
  }
  return {
    payload: {
      name: values.name,
      mode: "builtin",
      connector_key: "kubernetes",
      base_url: values.base_url,
      auth_flow: values.auth_flow as AuthFlow,
      auth_config: {},
      spec_url: values.spec_url || null,
      credentials,
    },
    valid,
    summary: {
      authMethodLabel:
        values.auth_flow === "basic" ? "Basic auth" : "Bearer token (service account)",
      secretSummary:
        values.auth_flow === "basic"
          ? values.username
            ? `${values.username} · ${maskSecret(values.token) ?? "(no password)"}`
            : null
          : maskSecret(values.token),
      isOAuth: false,
      oauthProvider: null,
    },
  };
}

function KubernetesForm({
  onSubmit,
  submitting,
  embedded,
  onNameChange,
  onStateChange,
}: SubFormProps) {
  const form = useForm<KubernetesValues>({
    resolver: zodResolver(kubernetesSchema),
    defaultValues: { name: "kubernetes", auth_flow: "bearer", base_url: "" },
  });
  const flow = form.watch("auth_flow");
  const nameValue = form.watch("name");
  useEffect(() => { onNameChange?.(nameValue); }, [nameValue, onNameChange]);
  useEmitState(form, onStateChange, buildKubernetesState);

  function handle(values: KubernetesValues) {
    onSubmit?.(buildKubernetesState(values).payload);
  }

  return (
    <FormSection title="Connect Kubernetes">
      <Field label="Connection name" htmlFor="name">
        <Input id="name" {...form.register("name")} />
      </Field>
      <Field label="Base URL" htmlFor="base_url" error={form.formState.errors.base_url?.message}>
        <Input id="base_url" placeholder="https://k8s.mycompany.com:6443" {...form.register("base_url")} />
      </Field>
      <Field label="Spec URL" htmlFor="spec_url" hint="Optional — e.g. https://k8s.mycompany.com:6443/openapi/v2" error={form.formState.errors.spec_url?.message}>
        <Input id="spec_url" placeholder="https://k8s.mycompany.com:6443/openapi/v2" {...form.register("spec_url")} />
      </Field>
      <Field label="Auth method" htmlFor="auth_flow">
        <Select id="auth_flow" {...form.register("auth_flow")}>
          <option value="bearer">Bearer token (service account)</option>
          <option value="basic">Basic auth</option>
        </Select>
      </Field>
      {flow === "basic" && (
        <>
          <Field label="Username" htmlFor="username">
            <Input id="username" {...form.register("username")} />
          </Field>
          <Field label="Password" htmlFor="token">
            <Input id="token" type="password" autoComplete="off" {...form.register("token")} />
          </Field>
        </>
      )}
      {flow === "bearer" && (
        <Field label="Bearer token" htmlFor="token">
          <Input id="token" type="password" autoComplete="off" {...form.register("token")} />
        </Field>
      )}
      {!embedded && (
        <div className="flex justify-end">
          <Button onClick={form.handleSubmit(handle)} disabled={submitting}>
            {submitting ? "Creating…" : "Create connection"}
          </Button>
        </div>
      )}
    </FormSection>
  );
}

// ── Linear ────────────────────────────────────────────────────────────────────

const linearSchema = z.object({
  name: z.string().min(1, "Required"),
  spec_url: z.string().url("Must be a valid URL").optional().or(z.literal("")),
  auth_flow: z.enum(["bearer", "oauth_authcode"]),
  token: z.string().optional(),
});
type LinearValues = z.infer<typeof linearSchema>;

function buildLinearState(values: LinearValues): WizardFormState {
  const valid =
    Boolean(values.name?.trim()) &&
    (values.auth_flow !== "bearer" || Boolean(values.token?.trim()));
  return {
    payload: {
      name: values.name,
      mode: "builtin",
      connector_key: "linear",
      auth_flow: values.auth_flow as AuthFlow,
      auth_config: {},
      spec_url: values.spec_url || null,
      credentials: values.auth_flow === "bearer" && values.token ? { token: values.token } : {},
    },
    valid,
    summary: {
      authMethodLabel:
        values.auth_flow === "bearer" ? "Personal API key" : "OAuth (sign in with Linear)",
      secretSummary:
        values.auth_flow === "bearer" ? maskSecret(values.token) ?? "(not set)" : null,
      isOAuth: values.auth_flow === "oauth_authcode",
      oauthProvider: values.auth_flow === "oauth_authcode" ? "Linear" : null,
    },
  };
}

function LinearForm({ onSubmit, submitting, embedded, onNameChange, onStateChange }: SubFormProps) {
  const form = useForm<LinearValues>({
    resolver: zodResolver(linearSchema),
    defaultValues: { name: "linear", auth_flow: "bearer", token: "" },
  });
  const flow = form.watch("auth_flow");
  const nameValue = form.watch("name");
  useEffect(() => { onNameChange?.(nameValue); }, [nameValue, onNameChange]);
  useEmitState(form, onStateChange, buildLinearState);

  function handle(values: LinearValues) {
    onSubmit?.(buildLinearState(values).payload);
  }

  return (
    <FormSection title="Connect Linear">
      <Field label="Connection name" htmlFor="name">
        <Input id="name" {...form.register("name")} />
      </Field>
      <Field label="Spec URL" htmlFor="spec_url" hint="Optional — community-curated OpenAPI spec" error={form.formState.errors.spec_url?.message}>
        <Input id="spec_url" placeholder="https://example.com/linear-openapi.json" {...form.register("spec_url")} />
      </Field>
      <Field label="Auth method" htmlFor="auth_flow">
        <Select id="auth_flow" {...form.register("auth_flow")}>
          <option value="bearer">Personal API key</option>
        </Select>
      </Field>
      {flow === "bearer" && (
        <Field
          label="Personal API key"
          htmlFor="token"
          hint="Sent only to Harnex; stored encrypted in Infisical, never in the browser."
          error={form.formState.errors.token?.message}
        >
          <Input id="token" type="password" autoComplete="off" {...form.register("token")} />
        </Field>
      )}
      {flow === "oauth_authcode" && (
        <OAuthConsent provider="Linear" />
      )}
      {!embedded && (
        <div className="flex justify-end">
          <Button onClick={form.handleSubmit(handle)} disabled={submitting}>
            {submitting ? "Creating…" : "Create connection"}
          </Button>
        </div>
      )}
    </FormSection>
  );
}

// ── Slack ─────────────────────────────────────────────────────────────────────

const slackSchema = z.object({
  name: z.string().min(1, "Required"),
  auth_flow: z.enum(["bearer", "oauth_authcode"]),
  token: z.string().optional(),
});
type SlackValues = z.infer<typeof slackSchema>;

function buildSlackState(values: SlackValues): WizardFormState {
  const valid =
    Boolean(values.name?.trim()) &&
    (values.auth_flow !== "bearer" || Boolean(values.token?.trim()));
  return {
    payload: {
      name: values.name,
      mode: "builtin",
      connector_key: "slack",
      auth_flow: values.auth_flow as AuthFlow,
      auth_config: {},
      credentials: values.auth_flow === "bearer" && values.token ? { token: values.token } : {},
    },
    valid,
    summary: {
      authMethodLabel: values.auth_flow === "bearer" ? "Bot token" : "OAuth (user token)",
      secretSummary:
        values.auth_flow === "bearer" ? maskSecret(values.token) ?? "(not set)" : null,
      isOAuth: values.auth_flow === "oauth_authcode",
      oauthProvider: values.auth_flow === "oauth_authcode" ? "Slack" : null,
    },
  };
}

function SlackForm({ onSubmit, submitting, embedded, onNameChange, onStateChange }: SubFormProps) {
  const form = useForm<SlackValues>({
    resolver: zodResolver(slackSchema),
    defaultValues: { name: "slack", auth_flow: "bearer", token: "" },
  });
  const flow = form.watch("auth_flow");
  const nameValue = form.watch("name");
  useEffect(() => { onNameChange?.(nameValue); }, [nameValue, onNameChange]);
  useEmitState(form, onStateChange, buildSlackState);

  function handle(values: SlackValues) {
    onSubmit?.(buildSlackState(values).payload);
  }

  return (
    <FormSection title="Connect Slack">
      <Field label="Connection name" htmlFor="name">
        <Input id="name" {...form.register("name")} />
      </Field>
      <Field label="Auth method" htmlFor="auth_flow">
        <Select id="auth_flow" {...form.register("auth_flow")}>
          <option value="bearer">Bot token</option>
        </Select>
      </Field>
      {flow === "bearer" && (
        <Field
          label="Bot token"
          htmlFor="token"
          hint="Starts with xoxb-... — stored in Infisical, never in the browser."
          error={form.formState.errors.token?.message}
        >
          <Input id="token" type="password" autoComplete="off" {...form.register("token")} />
        </Field>
      )}
      {flow === "oauth_authcode" && (
        <OAuthConsent provider="Slack" />
      )}
      {!embedded && (
        <div className="flex justify-end">
          <Button onClick={form.handleSubmit(handle)} disabled={submitting}>
            {submitting ? "Creating…" : "Create connection"}
          </Button>
        </div>
      )}
    </FormSection>
  );
}

// ── Exports ───────────────────────────────────────────────────────────────────

export function BuiltinConnectorForm({
  connectorKey,
  onSubmit,
  submitting,
  embedded,
  onNameChange,
  onStateChange,
}: Props) {
  const shared: SubFormProps = {
    onSubmit,
    submitting,
    embedded,
    onNameChange,
    onStateChange,
  };
  switch (connectorKey) {
    case "github":
      return <GithubForm {...shared} />;
    case "jenkins":
      return <JenkinsForm {...shared} />;
    case "gitlab":
      return <GitLabForm {...shared} />;
    case "jira":
      return <JiraForm {...shared} />;
    case "kubernetes":
      return <KubernetesForm {...shared} />;
    case "linear":
      return <LinearForm {...shared} />;
    case "slack":
      return <SlackForm {...shared} />;
    default:
      return null;
  }
}

// ── Shared layout primitives (used by other wizard steps) ─────────────────────

export function FormCard({
  title,
  hint,
  children,
}: {
  title: string;
  hint?: string;
  children: ReactNode;
}) {
  return (
    <section style={{ display: "flex", flexDirection: "column", gap: 18 }}>
      <div style={{ borderBottom: "1px solid var(--border)", paddingBottom: 12 }}>
        <div style={{ fontSize: 15, fontWeight: 600, color: "var(--ink)", marginBottom: hint ? 4 : 0 }}>
          {title}
        </div>
        {hint && (
          <div style={{ fontSize: 12.5, color: "var(--muted)" }}>{hint}</div>
        )}
      </div>
      {children}
    </section>
  );
}

export function FormField({
  label,
  htmlFor,
  hint,
  error,
  children,
}: {
  label: string;
  htmlFor: string;
  hint?: string;
  error?: string;
  children: ReactNode;
}) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
      <label
        htmlFor={htmlFor}
        style={{ fontSize: 12.5, fontWeight: 500, color: "var(--slate)" }}
      >
        {label}
      </label>
      {children}
      {hint && !error && (
        <span style={{ fontSize: 11.5, color: "var(--muted)" }}>{hint}</span>
      )}
      {error && (
        <span style={{ fontSize: 11.5, color: "var(--red)" }}>{error}</span>
      )}
    </div>
  );
}

export function FormActions({
  submitting,
  onSubmit,
  disabled,
}: {
  submitting: boolean;
  onSubmit: () => void;
  disabled?: boolean;
}) {
  return (
    <div style={{ display: "flex", justifyContent: "flex-end", paddingTop: 4 }}>
      <button
        className="btn btn-accent"
        onClick={onSubmit}
        disabled={submitting || disabled}
      >
        {submitting ? "Creating…" : "Create connection"}
      </button>
    </div>
  );
}
