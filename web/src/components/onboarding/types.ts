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
