import type { AuthFlow, CreateConnectionInput } from "@/lib/api";

export interface WizardSummary {
  /** Human-readable label for the chosen auth method. */
  authMethodLabel: string;
  /** Masked or descriptive summary of the credential, or null for OAuth/none. */
  secretSummary: string | null;
  isOAuth: boolean;
  oauthProvider: string | null;
}

export interface WizardFormState {
  payload: CreateConnectionInput;
  file?: File | null;
  /** True when the underlying form passes its zod schema. */
  valid: boolean;
  summary: WizardSummary;
}

export function maskSecret(value: string | undefined | null): string | null {
  if (!value) return null;
  const trimmed = value.trim();
  if (!trimmed) return null;
  const head = trimmed.slice(0, 4);
  return `${head}${"•".repeat(Math.min(8, Math.max(4, trimmed.length - 4)))}`;
}

export function authMethodLabel(flow: AuthFlow): string {
  switch (flow) {
    case "none":
      return "None / public";
    case "bearer":
      return "Bearer token";
    case "basic":
      return "Basic auth";
    case "api_key_header":
      return "API key (header)";
    case "api_key_query":
      return "API key (query)";
    case "oauth_authcode":
      return "OAuth (auth code)";
    case "oauth_clientcred":
      return "OAuth (client credentials)";
  }
}
