import type { MarkKey } from "./marks";

export interface ProfileState {
  fullName: string;
  handle: string;
}

export interface OrgState {
  orgName: string;
  teamSize: TeamSize;
}

export interface ConnectionState {
  connection: MarkKey | null;
  /** Optional friendly name forwarded to createConnection; defaults from connector picker. */
  displayName: string;
}

export type TeamSize = "Just me" | "2-10" | "11-50" | "51+";

export const TEAM_SIZES: TeamSize[] = ["Just me", "2-10", "11-50", "51+"];

export interface ConnectorOption {
  key: MarkKey;
  name: string;
  kind: string;
}

export const POPULAR_CONNECTIONS: ConnectorOption[] = [
  { key: "github", name: "GitHub", kind: "Source control" },
  { key: "openai", name: "OpenAI", kind: "LLM provider" },
  { key: "anthropic", name: "Anthropic", kind: "LLM provider" },
  { key: "postgres", name: "Postgres", kind: "Database" },
  { key: "stripe", name: "Stripe", kind: "Payments" },
  { key: "slack", name: "Slack", kind: "Messaging" },
  { key: "linear", name: "Linear", kind: "Issue tracker" },
  { key: "supabase", name: "Supabase", kind: "Backend" },
];

/** Orbiting mono labels per connector — must cover 12 constellation wires (remainder cycles). */
const OUTER_PREVIEW: string[] = [
  "GET /health",
  "POST /webhook",
  "GET /v1/me",
  "PATCH /resource",
  "GET /search",
  "POST /batch",
];

export const CONNECTOR_WIRE_PREVIEW: Record<
  Exclude<MarkKey, "vercel" | "notion" | "aws" | "sentry">,
  readonly string[]
> = {
  github: [
    "GET /user",
    "GET /repos/{owner}/{repo}",
    "POST /repos/{issue}",
    "GET /orgs/{org}/repos",
    "POST /graphql",
    "GET /notifications",
    "GET /installation/token",
    "GET /repos/{owner}/{repo}/issues",
    "POST /repos/{owner}/{repo}/pulls",
    "GET /rate_limit",
    "GET /teams/{id}",
    "GET /repos/{owner}/{repo}/actions/runs",
  ],
  openai: [
    "POST /v1/chat/completions",
    "POST /v1/embeddings",
    "GET /v1/models",
    "POST /v1/responses",
    "POST /v1/images/generations",
    "POST /v1/audio/transcriptions",
    "GET /v1/fine-tuning/jobs",
    "POST /v1/moderations",
    "GET /v1/assistants",
    "POST /v1/threads/runs",
    "POST /v1/batches",
    "DELETE /v1/files/{id}",
  ],
  anthropic: [
    "POST /v1/messages",
    "POST /v1/complete",
    "GET /v1/models",
    "POST /v1/count_tokens",
    "GET /organizations/api_keys",
    "POST /v1/files",
    "GET /v1/batches",
    "POST /v1/batches/{id}",
    "GET /v1/beta/skills",
    "POST /v1/messages/count_tokens",
    "GET /v1/usage",
    "POST /v1/feedback",
  ],
  postgres: [
    "SELECT * FROM tenants",
    "INSERT INTO logs",
    "EXPLAIN ANALYZE",
    "LISTEN pg_notify",
    "COPY telemetry TO stdout",
    "PREPARE stmt AS",
    "BEGIN READ ONLY",
    "NOTIFY alerts",
    "ALTER TYPE enum",
    "VACUUM ANALYZE",
    "SHOW pool_status",
    "CREATE INDEX CONCURRENTLY",
  ],
  stripe: [
    "POST /v1/charges",
    "GET /v1/customers",
    "POST /v1/checkout/sessions",
    "POST /v1/payment_intents",
    "GET /v1/subscriptions/{id}",
    "POST /v1/refunds",
    "GET /v1/invoices/upcoming",
    "POST /v1/setup_intents",
    "POST /v1/webhook_endpoints",
    "GET /v1/products",
    "POST /v1/prices",
    "GET /v1/balance",
  ],
  slack: [
    "POST /chat.postMessage",
    "GET /users.list",
    "GET /conversations.history",
    "POST /views.open",
    "POST /files.upload",
    "GET /apps.connections.list",
    "POST /bookmarks.add",
    "GET /team.info",
    "POST /pins.add",
    "GET /emoji.list",
    "POST /workflows.stepCompleted",
    "GET /reactions.list",
  ],
  linear: [
    "POST /graphql",
    "mutation issueCreate",
    "query viewer",
    "mutation commentCreate",
    "query cycles",
    "mutation projectUpdate",
    "query workflowStates",
    "mutation labelCreate",
    "query integrationGithub",
    "mutation issueArchive",
    "query teams",
    "mutation webhookCreate",
  ],
  supabase: [
    "GET /rest/v1/profiles",
    "POST /auth/v1/token",
    "GET /storage/v1/object/list",
    "POST /functions/v1/edge-fn",
    "GET /realtime/v1/",
    "POST /rest/v1/rpc/exec_sql",
    "PATCH /rest/v1/rows",
    "DELETE /storage/v1/object/",
    "GET /rest/v1/?select=*",
    "POST /graphql/v1",
    "HEAD /rest/v1/health",
    "GET /auth/v1/user",
  ],
};

/** Labels for constellation when no hover/selection hint. */
export const DEFAULT_CONSTELLATION_LABELS: readonly string[] = OUTER_PREVIEW;

/** Extra connectors (marks only) reuse a plausible generic SaaS orbit. */
const GENERIC_REMOTE_LABELS: readonly string[] = [
  "GET /v2/resource",
  "POST /rpc/invoke",
  "GET /v1/schema",
  "PATCH /records/{id}",
  "POST /events/ingest",
  "DELETE /sessions/{id}",
  "GET /metrics",
  "POST /enqueue",
];

export function wireLabelsForConnector(key: MarkKey | null | undefined): readonly string[] {
  if (!key) return DEFAULT_CONSTELLATION_LABELS;
  const row = CONNECTOR_WIRE_PREVIEW[key as keyof typeof CONNECTOR_WIRE_PREVIEW];
  if (row) return row;
  return GENERIC_REMOTE_LABELS;
}
