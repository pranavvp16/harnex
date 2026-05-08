import type { UseFormReturn } from "react-hook-form";
import { z } from "zod";

import { FormField } from "@/components/wizard/BuiltinConnectorForm";

export const authConfigSchema = z.object({
  auth_flow: z.enum([
    "none",
    "api_key_header",
    "api_key_query",
    "bearer",
    "basic",
    "oauth_authcode",
    "oauth_clientcred",
  ]),
  header_name: z.string().optional(),
  query_name: z.string().optional(),
  prefix: z.string().optional(),
  api_key: z.string().optional(),
  token: z.string().optional(),
  username: z.string().optional(),
  password: z.string().optional(),
});

export type AuthValues = z.infer<typeof authConfigSchema>;

interface Props<T extends AuthValues> {
  form: UseFormReturn<T>;
}

export function AuthConfigSection<T extends AuthValues>({ form }: Props<T>) {
  const register = form.register as unknown as (name: string) => Record<string, unknown>;
  const flow = form.watch("auth_flow" as never) as unknown as AuthValues["auth_flow"];

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: 12,
        borderRadius: "var(--r-lg)",
        border: "1px solid var(--border)",
        background: "var(--surface-2)",
        padding: 16,
      }}
    >
      <div style={{ fontSize: 12, fontWeight: 600, color: "var(--ink)", letterSpacing: "0.04em", textTransform: "uppercase" }}>
        Authentication
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
        <label style={{ fontSize: 12.5, fontWeight: 500, color: "var(--slate)" }} htmlFor="auth_flow">
          Auth method
        </label>
        <select className="select" id="auth_flow" {...register("auth_flow")}>
          <option value="none">None / public</option>
          <option value="bearer">Bearer token</option>
          <option value="api_key_header">API key (header)</option>
          <option value="api_key_query">API key (query param)</option>
          <option value="basic">Basic auth</option>
          <option value="oauth_authcode">OAuth (auth code)</option>
          <option value="oauth_clientcred">OAuth (client credentials)</option>
        </select>
      </div>

      {flow === "api_key_header" && (
        <>
          <FormField label="Header name" htmlFor="header_name" hint="e.g. X-API-Key">
            <input className="input" id="header_name" placeholder="X-API-Key" {...register("header_name")} />
          </FormField>
          <FormField label="Prefix" htmlFor="prefix" hint="e.g. 'Bearer ' — leave blank if none">
            <input className="input" id="prefix" {...register("prefix")} />
          </FormField>
          <FormField label="API key" htmlFor="api_key">
            <input className="input" id="api_key" type="password" autoComplete="off" {...register("api_key")} />
          </FormField>
        </>
      )}

      {flow === "api_key_query" && (
        <>
          <FormField label="Query param name" htmlFor="query_name" hint="e.g. api_key">
            <input className="input" id="query_name" placeholder="api_key" {...register("query_name")} />
          </FormField>
          <FormField label="API key" htmlFor="api_key">
            <input className="input" id="api_key" type="password" autoComplete="off" {...register("api_key")} />
          </FormField>
        </>
      )}

      {flow === "bearer" && (
        <FormField label="Token" htmlFor="token">
          <input className="input" id="token" type="password" autoComplete="off" {...register("token")} />
        </FormField>
      )}

      {flow === "basic" && (
        <>
          <FormField label="Username" htmlFor="username">
            <input className="input" id="username" {...register("username")} />
          </FormField>
          <FormField label="Password" htmlFor="password">
            <input className="input" id="password" type="password" autoComplete="off" {...register("password")} />
          </FormField>
        </>
      )}

      {(flow === "oauth_authcode" || flow === "oauth_clientcred") && (
        <p style={{ fontSize: 13, color: "var(--slate)", margin: 0, lineHeight: 1.6 }}>
          OAuth credentials are configured per connector. After creating the connection
          we&apos;ll guide you through the OAuth flow.
        </p>
      )}
    </div>
  );
}
