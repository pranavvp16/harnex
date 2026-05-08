import { useMemo } from "react";

import { useAuth } from "@/lib/auth";
import { buildClient, type HarnexClient } from "@/lib/api";

export function useApi(): HarnexClient {
  const { getAccessToken, devTenantId } = useAuth();
  return useMemo(
    () => buildClient({ getAccessToken, devTenantId }),
    [getAccessToken, devTenantId],
  );
}
