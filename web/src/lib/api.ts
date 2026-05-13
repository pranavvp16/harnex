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

export type ExecutionMode = "code" | "structured";
export type ExecutionStatus = "pending" | "success" | "error" | "timeout";

export interface Connector {
  key: string;
  display_name: string;
  is_builtin: boolean;
  default_base_url: string | null;
  supported_auth: AuthFlow[];
}

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
  auth_config: Record<string, unknown>;
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

export interface ReindexResult {
  connection_id: string;
  operation_count: number;
  chunk_count: number;
  spec_hash: string | null;
}

export type ApiKeyScopeType = "all" | "connections";

export interface ApiKeyScope {
  type: ApiKeyScopeType;
  connection_ids: string[];
}

export interface ApiKey {
  id: string;
  name: string;
  key_prefix: string;
  is_active: boolean;
  created_at: string;
  last_used_at: string | null;
  expires_at: string | null;
  scope: ApiKeyScope;
}

export interface IssuedApiKey extends ApiKey {
  /** Plaintext token — only returned once at creation. */
  plaintext: string;
}

export interface IssueApiKeyInput {
  name: string;
  scope: ApiKeyScope;
  /** None = never expires; otherwise a positive day count. */
  expires_in_days: number | null;
}

export interface ConnectionTestInput {
  mode: ConnectionMode;
  connector_key?: string | null;
  base_url?: string | null;
  auth_flow: AuthFlow;
  auth_config?: Record<string, unknown>;
  credentials?: Record<string, string>;
}

export interface ConnectionTestResult {
  ok: boolean;
  http_status: number | null;
  method: string;
  url: string;
  error_kind: string | null;
  message: string;
  duration_ms: number;
  metadata?: Record<string, string>;
}

export interface ExecutionLogItem {
  id: string;
  tenant_id: string;
  connection_id: string | null;
  status: ExecutionStatus;
  mode: ExecutionMode;
  operation_id: string | null;
  method: string | null;
  path: string | null;
  request_summary: Record<string, unknown>;
  response_summary: Record<string, unknown>;
  duration_ms: number | null;
  error_kind: string | null;
  error_message: string | null;
  created_at: string;
}

export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface UsageCurrent {
  year_month: string;
  executions: number;
  searches: number;
  embedding_tokens: number;
  monthly_execution_quota: number;
}

export type TenantPlan = "free" | "starter" | "pro" | "enterprise";
export type TenantRole = "owner" | "admin" | "developer" | "viewer";

export interface Tenant {
  id: string;
  slug: string;
  display_name: string;
  plan: TenantPlan;
  created_at: string;
}

export interface TenantMembership {
  id: string;
  tenant_id: string;
  email: string | null;
  role: TenantRole;
  tenant: Tenant;
}

export interface MeResponse {
  user: { id: string; email: string | null; full_name: string | null };
  memberships: TenantMembership[];
  current_tenant_id: string | null;
}

export interface CreateTenantInput {
  display_name: string;
  slug?: string | null;
  team_size?: string | null;
  profile: {
    full_name: string;
    handle?: string | null;
    email?: string | null;
  };
}

export interface SlugCheckResult {
  slug: string;
  available: boolean;
}

export interface SearchHit {
  operation_id: string;
  connection_id: string;
  connector_key: string | null;
  method: string;
  path: string;
  summary: string;
  score: number;
}

export interface SearchResponse {
  hits: SearchHit[];
  clarification_needed: boolean;
  candidate_connectors: string[];
}

export interface ExecuteRequestInput {
  connection_id: string;
  operation_id: string;
  path_params?: Record<string, unknown>;
  query?: Record<string, unknown>;
  headers?: Record<string, string>;
  body?: unknown;
}

export interface FileItem {
  id: string;
  filename: string;
  content_type: string;
  size_bytes: number;
  skill_key: string;
  download_url: string;
  download_url_expires_at: string;
  created_at: string;
}

export interface ListFilesInput {
  limit?: number;
  offset?: number;
  skillKey?: string | null;
}

export interface ExecuteResponse {
  status: ExecutionStatus;
  http_status: number | null;
  body: unknown;
  headers: Record<string, string>;
  error_kind: string | null;
  error_message: string | null;
  duration_ms: number | null;
  operation_id: string | null;
  method: string | null;
  path: string | null;
}

type TokenGetter = () => Promise<string | null>;

export interface ClientAuth {
  /** Returns a JWT access token for production OIDC auth. */
  getAccessToken: TokenGetter;
  /** Local dev: send X-Harnex-Dev-Tenant header instead of a bearer JWT. */
  devTenantId?: string | null;
}

export interface HarnexClient {
  listConnectors(): Promise<Connector[]>;
  listConnections(): Promise<Connection[]>;
  getConnection(id: string): Promise<Connection>;
  createConnection(input: CreateConnectionInput): Promise<Connection>;
  testConnection(input: ConnectionTestInput): Promise<ConnectionTestResult>;
  reindexConnection(id: string): Promise<ReindexResult>;
  deleteConnection(id: string): Promise<void>;
  uploadOpenApiSpec(id: string, file: File): Promise<ReindexResult>;
  listApiKeys(): Promise<ApiKey[]>;
  issueApiKey(input: IssueApiKeyInput): Promise<IssuedApiKey>;
  revokeApiKey(id: string): Promise<void>;
  listExecutions(params?: { limit?: number; offset?: number }): Promise<Page<ExecutionLogItem>>;
  getCurrentUsage(): Promise<UsageCurrent>;
  search(input: {
    query: string;
    top_k?: number;
    connector_filter?: string | null;
  }): Promise<SearchResponse>;
  executeOperation(input: ExecuteRequestInput): Promise<ExecuteResponse>;
  listFiles(input?: ListFilesInput): Promise<Page<FileItem>>;
  deleteFile(id: string): Promise<void>;
  getMe(): Promise<MeResponse>;
  createTenant(input: CreateTenantInput): Promise<Tenant>;
  checkTenantSlug(slug: string): Promise<SlugCheckResult>;
}

export function buildClient(auth: ClientAuth | TokenGetter): HarnexClient {
  const cfg: ClientAuth = typeof auth === "function" ? { getAccessToken: auth } : auth;

  async function call<T>(
    path: string,
    init: RequestInit & { json?: unknown } = {},
  ): Promise<T> {
    const headers = new Headers(init.headers);
    const token = await cfg.getAccessToken();
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
      // Real-auth path: tell the API which workspace to scope to. Backend
      // verifies the caller actually has membership in this tenant.
      if (cfg.devTenantId) headers.set("X-Harnex-Tenant", cfg.devTenantId);
    } else if (cfg.devTenantId) {
      // Dev-mode build with no Keycloak — header-only auth for local testing.
      headers.set("X-Harnex-Dev-Tenant", cfg.devTenantId);
    }
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
    listConnectors: () => call<Connector[]>("/v1/connectors"),
    listConnections: () => call<Connection[]>("/v1/connections"),
    getConnection: (id) => call<Connection>(`/v1/connections/${id}`),
    createConnection: (input) =>
      call<Connection>("/v1/connections", { method: "POST", json: input }),
    testConnection: (input) =>
      call<ConnectionTestResult>("/v1/connections/test", { method: "POST", json: input }),
    reindexConnection: (id) =>
      call<ReindexResult>(`/v1/connections/${id}/reindex`, { method: "POST" }),
    deleteConnection: (id) => call<void>(`/v1/connections/${id}`, { method: "DELETE" }),
    uploadOpenApiSpec: async (id, file) => {
      const fd = new FormData();
      fd.append("file", file);
      return call<ReindexResult>(`/v1/connections/${id}/spec`, { method: "POST", body: fd });
    },
    listApiKeys: () => call<ApiKey[]>("/v1/api-keys"),
    issueApiKey: (input) =>
      call<IssuedApiKey>("/v1/api-keys", { method: "POST", json: input }),
    revokeApiKey: (id) => call<void>(`/v1/api-keys/${id}`, { method: "DELETE" }),
    listExecutions: ({ limit = 50, offset = 0 } = {}) =>
      call<Page<ExecutionLogItem>>(`/v1/executions?limit=${limit}&offset=${offset}`),
    getCurrentUsage: () => call<UsageCurrent>("/v1/usage/current"),
    search: (input) =>
      call<SearchResponse>("/v1/search", {
        method: "POST",
        json: {
          query: input.query,
          top_k: input.top_k ?? 10,
          connector_filter: input.connector_filter ?? null,
        },
      }),
    executeOperation: (input) =>
      call<ExecuteResponse>("/v1/execute", { method: "POST", json: input }),
    listFiles: ({ limit = 50, offset = 0, skillKey = null } = {}) => {
      const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
      if (skillKey) params.set("skill_key", skillKey);
      return call<Page<FileItem>>(`/v1/files?${params.toString()}`);
    },
    deleteFile: (id) => call<void>(`/v1/files/${id}`, { method: "DELETE" }),
    getMe: () => call<MeResponse>("/v1/me"),
    createTenant: (input) =>
      call<Tenant>("/v1/tenants", { method: "POST", json: input }),
    checkTenantSlug: (slug) =>
      call<SlugCheckResult>(`/v1/tenants/check-slug?slug=${encodeURIComponent(slug)}`),
  };
}
