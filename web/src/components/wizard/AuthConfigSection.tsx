import type { UseFormReturn } from "react-hook-form";
import { z } from "zod";

import { Field } from "@/components/ui/Field";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";

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
  // react-hook-form's generic register signature accepts any string Path; cast at use-site.
  const register = form.register as unknown as (name: string) => Record<string, unknown>;
  const flow = form.watch("auth_flow" as never) as AuthValues["auth_flow"];

  return (
    <div className="flex flex-col gap-3 rounded-lg border border-slate-100 bg-slate-50 p-4">
      <h3 className="text-sm font-semibold text-slate-700">Authentication</h3>
      <Field label="Auth method" htmlFor="auth_flow">
        <Select id="auth_flow" {...register("auth_flow")}>
          <option value="none">None / public</option>
          <option value="bearer">Bearer token</option>
          <option value="api_key_header">API key (header)</option>
          <option value="api_key_query">API key (query param)</option>
          <option value="basic">Basic auth</option>
          <option value="oauth_authcode">OAuth (auth code)</option>
          <option value="oauth_clientcred">OAuth (client credentials)</option>
        </Select>
      </Field>

      {flow === "api_key_header" && (
        <>
          <Field label="Header name" htmlFor="header_name" hint="e.g. X-API-Key, Authorization">
            <Input id="header_name" placeholder="X-API-Key" {...register("header_name")} />
          </Field>
          <Field label="Prefix" htmlFor="prefix" hint="e.g. 'Bearer ' or 'token '. Leave blank if none.">
            <Input id="prefix" {...register("prefix")} />
          </Field>
          <Field label="API key" htmlFor="api_key">
            <Input id="api_key" type="password" autoComplete="off" {...register("api_key")} />
          </Field>
        </>
      )}

      {flow === "api_key_query" && (
        <>
          <Field label="Query parameter name" htmlFor="query_name" hint="e.g. api_key">
            <Input id="query_name" placeholder="api_key" {...register("query_name")} />
          </Field>
          <Field label="API key" htmlFor="api_key">
            <Input id="api_key" type="password" autoComplete="off" {...register("api_key")} />
          </Field>
        </>
      )}

      {flow === "bearer" && (
        <Field label="Token" htmlFor="token">
          <Input id="token" type="password" autoComplete="off" {...register("token")} />
        </Field>
      )}

      {flow === "basic" && (
        <>
          <Field label="Username" htmlFor="username">
            <Input id="username" {...register("username")} />
          </Field>
          <Field label="Password" htmlFor="password">
            <Input id="password" type="password" autoComplete="off" {...register("password")} />
          </Field>
        </>
      )}

      {(flow === "oauth_authcode" || flow === "oauth_clientcred") && (
        <p className="text-sm text-slate-600">
          OAuth client credentials are configured per connector. After creating the connection,
          we&apos;ll walk you through the OAuth flow.
        </p>
      )}
    </div>
  );
}
