import { useMemo } from "react";

import { buildClient, type HarnexClient } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { env } from "@/lib/env";

export function useApi(): HarnexClient {
  const { devTenantId } = useAuth();
  return useMemo(
    () =>
      buildClient({
        // Header-only dev tenant is only valid for dev builds (VITE_HARNEX_DEV_TENANT).
        // In real-auth builds the backend resolves the tenant from the cookie session.
        devTenantId: env.devTenantId ? devTenantId : null,
      }),
    [devTenantId],
  );
}
