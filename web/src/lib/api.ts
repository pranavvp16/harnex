import { env } from "@/lib/env";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
    public readonly body: unknown,
  ) {
    super(message);
  }
}

export type AuthFlow =
  | "none"
  | "api_key_header"
  | "api_key_query"
  | "bearer"
  | "basic"
  | "oauth_authcode"
  | "oauth_clientcred";

export type ConnectionMode = "builtin" | "openapi_url" | "openapi_upload" | "bare_url";

export type ConnectionStatus = "pending" | "indexing" | "ready" | "error" | "disabled";

export interface Connection {
  id: string;
  tenant_id: string;
  connector_key: string | null;
  name: string;
  mode: ConnectionMode;
  status: ConnectionStatus;
  base_url: string | null;
  spec_url: string | null;
  auth_flow: AuthFlow;
  endpoint_count: number;
  last_indexed_at: string | null;
  last_error: string | null;
  created_at: string;
  updated_at: string;
}

export interface CreateConnectionInput {
  name: string;
  mode: ConnectionMode;
  connector_key?: string | null;
  base_url?: string | null;
  spec_url?: string | null;
  auth_flow: AuthFlow;
  /** Public auth shape (header name, prefix, query name) — never secret values. */
  auth_config?: Record<string, unknown>;
  /** Secret values; backend forwards to Infisical and never persists in Postgres. */
  credentials?: Record<string, string>;
}

export interface ApiKey {
  id: string;
  name: string;
  key_prefix: string;
  is_active: boolean;
  created_at: string;
  last_used_at: string | null;
}

export interface IssuedApiKey extends ApiKey {
  /** Plaintext token — only returned once at creation. */
  token: string;
}

export interface ExecutionLogItem {
  id: string;
  status: "pending" | "success" | "error" | "timeout";
  mode: "code" | "structured";
  operation_id: string | null;
  method: string | null;
  path: string | null;
  duration_ms: number | null;
  error_kind: string | null;
  created_at: string;
}

export interface UsageCurrent {
  year_month: string;
  executions: number;
  searches: number;
  embedding_tokens: number;
  monthly_execution_quota: number;
}

type TokenGetter = () => Promise<string | null>;

export interface HarnexClient {
  listConnections(): Promise<Connection[]>;
  getConnection(id: string): Promise<Connection>;
  createConnection(input: CreateConnectionInput): Promise<Connection>;
  reindexConnection(id: string): Promise<Connection>;
  deleteConnection(id: string): Promise<void>;
  uploadOpenApiSpec(id: string, file: File): Promise<Connection>;
  listApiKeys(): Promise<ApiKey[]>;
  issueApiKey(name: string): Promise<IssuedApiKey>;
  revokeApiKey(id: string): Promise<void>;
  listExecutions(limit?: number): Promise<ExecutionLogItem[]>;
  getCurrentUsage(): Promise<UsageCurrent>;
}

export function buildClient(getToken: TokenGetter): HarnexClient {
  async function call<T>(
    path: string,
    init: RequestInit & { json?: unknown } = {},
  ): Promise<T> {
    const token = await getToken();
    const headers = new Headers(init.headers);
    if (token) headers.set("Authorization", `Bearer ${token}`);
    if (init.json !== undefined) {
      headers.set("content-type", "application/json");
    }
    const resp = await fetch(`${env.apiUrl}${path}`, {
      ...init,
      headers,
      body: init.json !== undefined ? JSON.stringify(init.json) : init.body,
    });
    if (!resp.ok) {
      let body: unknown = null;
      try {
        body = await resp.json();
      } catch {
        body = await resp.text();
      }
      throw new ApiError(resp.status, `${init.method ?? "GET"} ${path} -> ${resp.status}`, body);
    }
    if (resp.status === 204) return undefined as T;
    return (await resp.json()) as T;
  }

  return {
    listConnections: () => call<Connection[]>("/v1/connections"),
    getConnection: (id) => call<Connection>(`/v1/connections/${id}`),
    createConnection: (input) =>
      call<Connection>("/v1/connections", { method: "POST", json: input }),
    reindexConnection: (id) =>
      call<Connection>(`/v1/connections/${id}/reindex`, { method: "POST" }),
    deleteConnection: (id) => call<void>(`/v1/connections/${id}`, { method: "DELETE" }),
    uploadOpenApiSpec: async (id, file) => {
      const fd = new FormData();
      fd.append("spec", file);
      return call<Connection>(`/v1/connections/${id}/spec`, { method: "POST", body: fd });
    },
    listApiKeys: () => call<ApiKey[]>("/v1/api-keys"),
    issueApiKey: (name) => call<IssuedApiKey>("/v1/api-keys", { method: "POST", json: { name } }),
    revokeApiKey: (id) => call<void>(`/v1/api-keys/${id}`, { method: "DELETE" }),
    listExecutions: (limit = 50) => call<ExecutionLogItem[]>(`/v1/executions?limit=${limit}`),
    getCurrentUsage: () => call<UsageCurrent>("/v1/usage/current"),
  };
}
