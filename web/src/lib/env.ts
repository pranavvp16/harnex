function required(name: string, value: string | undefined): string {
  if (!value) {
    throw new Error(`Missing required env var: ${name}`);
  }
  return value;
}

export const env = {
  apiUrl: import.meta.env.VITE_HARNEX_API_URL ?? "/v1",
  keycloak: {
    authority: required("VITE_KEYCLOAK_AUTHORITY", import.meta.env.VITE_KEYCLOAK_AUTHORITY),
    clientId: required("VITE_KEYCLOAK_CLIENT_ID", import.meta.env.VITE_KEYCLOAK_CLIENT_ID),
    redirectUri: required("VITE_KEYCLOAK_REDIRECT_URI", import.meta.env.VITE_KEYCLOAK_REDIRECT_URI),
    postLogoutRedirectUri:
      import.meta.env.VITE_KEYCLOAK_POST_LOGOUT_REDIRECT_URI ?? window.location.origin,
  },
} as const;
