import { useMemo } from "react";

import { useAuth } from "@/lib/auth";
import { buildClient, type HarnexClient } from "@/lib/api";

export function useApi(): HarnexClient {
  const { getAccessToken } = useAuth();
  return useMemo(() => buildClient(getAccessToken), [getAccessToken]);
}
