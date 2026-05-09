import { useMemo } from "react";

import { buildClient, type HarnexClient } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { env } from "@/lib/env";

export function useApi(): HarnexClient {
  const { getAccessToken, devTenantId } = useAuth();
  return useMemo(
    () =>
      buildClient({
        getAccessToken,
        // Header-only dev tenant is only valid when OIDC was disabled at build time.
        // Otherwise we must always send the Keycloak access token.
        devTenantId: env.keycloak ? null : devTenantId,
      }),
    [getAccessToken, devTenantId],
  );
}
