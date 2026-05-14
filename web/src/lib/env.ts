const devTenantId = (import.meta.env.VITE_HARNEX_DEV_TENANT as string | undefined) || null;

/** Base URL for REST calls — no trailing slash. Empty string = same origin (Vite proxies `/v1`). */
const rawApiUrl = (import.meta.env.VITE_HARNEX_API_URL as string | undefined)?.trim();
const apiUrl = rawApiUrl ? rawApiUrl.replace(/\/$/, "") : "";

export const env = {
  apiUrl,
  /** When set, frontend skips OIDC and authenticates via the X-Harnex-Dev-Tenant header. */
  devTenantId,
} as const;
