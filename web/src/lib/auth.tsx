import { useQueryClient } from "@tanstack/react-query";
import { User, UserManager, WebStorageStateStore } from "oidc-client-ts";
import {
  type ReactNode,
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import { env } from "@/lib/env";

const ACTIVE_TENANT_STORAGE_KEY = "harnex.activeTenantId";

function readStoredTenantId(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return window.localStorage.getItem(ACTIVE_TENANT_STORAGE_KEY);
  } catch {
    return null;
  }
}

export type IdpHint = "google" | "github";

export interface SignInOptions {
  idpHint?: IdpHint;
  returnTo?: string;
}

export interface PasswordCredentials {
  email: string;
  password: string;
}

export interface RegisterInput {
  email: string;
  password: string;
  fullName: string;
}

export class AuthError extends Error {
  constructor(
    message: string,
    public readonly code?: string,
    public readonly status?: number,
  ) {
    super(message);
  }
}

export interface AuthState {
  status: "loading" | "anonymous" | "authenticated";
  user: User | null;
  manager: UserManager | null;
  signIn: (opts?: SignInOptions) => Promise<void>;
  signInWithPassword: (creds: PasswordCredentials) => Promise<void>;
  register: (input: RegisterInput) => Promise<void>;
  signOut: () => Promise<void>;
  getAccessToken: () => Promise<string | null>;
  /** Active tenant id for dev-header mode (VITE_HARNEX_DEV_TENANT build). Ignored for API auth when Keycloak is enabled. */
  devTenantId: string | null;
  /** Persist the active tenant id (used after onboarding creates a workspace). */
  setActiveTenantId: (id: string | null) => void;
}

const AuthContext = createContext<AuthState | null>(null);

function buildUserManager(): UserManager | null {
  if (!env.keycloak) return null;
  return new UserManager({
    authority: env.keycloak.authority,
    client_id: env.keycloak.clientId,
    redirect_uri: env.keycloak.redirectUri,
    post_logout_redirect_uri: env.keycloak.postLogoutRedirectUri,
    response_type: "code",
    scope: "openid profile email",
    automaticSilentRenew: true,
    userStore: new WebStorageStateStore({ store: window.sessionStorage }),
    monitorSession: false,
  });
}

interface AuthProviderProps {
  children: (auth: AuthState) => ReactNode;
}

interface KeycloakTokenResponse {
  access_token: string;
  refresh_token?: string;
  id_token?: string;
  token_type: string;
  expires_in: number;
  scope?: string;
  error?: string;
  error_description?: string;
}

function decodeJwtPayload(token: string): Record<string, unknown> {
  const segment = token.split(".")[1];
  if (!segment) return {};
  const padded = segment.replace(/-/g, "+").replace(/_/g, "/");
  const padLen = (4 - (padded.length % 4)) % 4;
  try {
    const decoded = atob(padded + "=".repeat(padLen));
    return JSON.parse(decoded) as Record<string, unknown>;
  } catch {
    return {};
  }
}

interface AuthMeResponse {
  sub: string;
  email: string | null;
  full_name: string | null;
  memberships: Array<{ id: string; tenant_id: string; role: string }>;
}

async function fetchAuthMe(token: string): Promise<AuthMeResponse | null> {
  try {
    const resp = await fetch(`${env.apiUrl}/v1/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!resp.ok) return null;
    return (await resp.json()) as AuthMeResponse;
  } catch {
    return null;
  }
}

/** Pick the tenant for this signed-in user, ignoring stale `prefer` ids the
 *  user no longer belongs to. */
function chooseTenant(me: AuthMeResponse, prefer: string | null): string | null {
  const ids = me.memberships.map((m) => m.tenant_id);
  if (prefer && ids.includes(prefer)) return prefer;
  return ids[0] ?? null;
}

function userFromTokenResponse(resp: KeycloakTokenResponse): User {
  const idClaims = resp.id_token ? decodeJwtPayload(resp.id_token) : {};
  const accessClaims = decodeJwtPayload(resp.access_token);
  const profile = (Object.keys(idClaims).length > 0 ? idClaims : accessClaims) as User["profile"];
  const expiresAt = Math.floor(Date.now() / 1000) + resp.expires_in;
  return new User({
    access_token: resp.access_token,
    refresh_token: resp.refresh_token,
    id_token: resp.id_token,
    token_type: resp.token_type,
    scope: resp.scope ?? "openid profile email",
    profile,
    expires_at: expiresAt,
    session_state: null,
    url_state: undefined,
  });
}

export function AuthProvider({ children }: AuthProviderProps) {
  const queryClient = useQueryClient();
  const manager = useMemo(buildUserManager, []);
  const [user, setUser] = useState<User | null>(null);
  // env.devTenantId means a dev-mode build (no Keycloak). Real builds start
  // with no active tenant — we only set one once the user is signed in and
  // we know they actually own that workspace.
  const [activeTenantId, setActiveTenantIdState] = useState<string | null>(
    () => env.devTenantId ?? null,
  );
  // Track the previously-active tenant so we can purge cached responses on
  // any switch — server-side scoping is correct, but stale cache from a
  // prior tenant must not flash to the new one.
  const previousTenantId = useRef<string | null>(activeTenantId);
  // Always start in "loading" (real Keycloak path). Dev-mode build with the
  // build-time devTenantId is the only no-auth bypass.
  const [status, setStatus] = useState<AuthState["status"]>(() =>
    !manager && env.devTenantId ? "authenticated" : "loading",
  );

  const setActiveTenantId = useCallback(
    (id: string | null) => {
      // If the tenant actually changed, drop every cached query — none of the
      // previous tenant's data is valid for the new one.
      if (previousTenantId.current !== id) {
        queryClient.clear();
        previousTenantId.current = id;
      }
      setActiveTenantIdState(id);
      if (typeof window === "undefined") return;
      try {
        if (id) window.localStorage.setItem(ACTIVE_TENANT_STORAGE_KEY, id);
        else window.localStorage.removeItem(ACTIVE_TENANT_STORAGE_KEY);
      } catch {
        // localStorage can fail in private mode — non-fatal, in-memory state still works.
      }
    },
    [queryClient],
  );

  useEffect(() => {
    if (!manager) {
      // Dev-mode build: build-time tenant means we're authenticated; otherwise anonymous.
      setStatus(env.devTenantId ? "authenticated" : "anonymous");
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const search = window.location.search;
        if (search.includes("code=") && search.includes("state=")) {
          const u = await manager.signinRedirectCallback();
          if (cancelled) return;
          setUser(u);
          const me = await fetchAuthMe(u.access_token);
          const tenant = me ? chooseTenant(me, readStoredTenantId()) : null;
          setActiveTenantId(tenant);
          setStatus("authenticated");
          const target = (u.state as { returnTo?: string } | null)?.returnTo ?? "/";
          window.history.replaceState({}, "", target);
          return;
        }
        const existing = await manager.getUser();
        if (existing && !existing.expired) {
          if (cancelled) return;
          setUser(existing);
          const me = await fetchAuthMe(existing.access_token);
          const tenant = me ? chooseTenant(me, readStoredTenantId()) : null;
          setActiveTenantId(tenant);
          setStatus("authenticated");
          return;
        }
        if (!cancelled) {
          // No session — drop any stale tenant id so the next login starts fresh.
          setActiveTenantId(null);
          setStatus("anonymous");
        }
      } catch (err) {
        console.error("auth bootstrap failed", err);
        if (!cancelled) setStatus("anonymous");
      }
    })();

    const onUserLoaded = (u: User) => {
      setUser(u);
      setStatus("authenticated");
    };
    const onUserUnloaded = () => {
      setUser(null);
      setStatus("anonymous");
    };
    manager.events.addUserLoaded(onUserLoaded);
    manager.events.addUserUnloaded(onUserUnloaded);
    return () => {
      cancelled = true;
      manager.events.removeUserLoaded(onUserLoaded);
      manager.events.removeUserUnloaded(onUserUnloaded);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- run once on manager init
  }, [manager]);

  const signIn = useCallback(
    async (opts: SignInOptions = {}) => {
      if (!manager) return;
      const extraQueryParams: Record<string, string> = {};
      if (opts.idpHint) extraQueryParams.kc_idp_hint = opts.idpHint;
      const returnTo =
        opts.returnTo ?? window.location.pathname + window.location.search;
      await manager.signinRedirect({
        state: { returnTo },
        extraQueryParams:
          Object.keys(extraQueryParams).length > 0 ? extraQueryParams : undefined,
      });
    },
    [manager],
  );

  const signInWithPassword = useCallback(
    async ({ email, password }: PasswordCredentials) => {
      if (!env.keycloak) {
        throw new AuthError("Keycloak is not configured for this build", "no_keycloak");
      }
      if (!manager) {
        throw new AuthError("Auth manager unavailable", "no_manager");
      }
      const tokenUrl = `${env.keycloak.authority.replace(/\/$/, "")}/protocol/openid-connect/token`;
      const body = new URLSearchParams({
        grant_type: "password",
        client_id: env.keycloak.clientId,
        username: email,
        password,
        scope: "openid profile email",
      });
      const resp = await fetch(tokenUrl, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body,
      });
      const data = (await resp.json()) as KeycloakTokenResponse;
      if (!resp.ok || !data.access_token) {
        throw new AuthError(
          data.error_description || data.error || "Sign in failed",
          data.error,
          resp.status,
        );
      }
      const u = userFromTokenResponse(data);
      await manager.storeUser(u);
      setUser(u);
      const me = await fetchAuthMe(u.access_token);
      const tenant = me ? chooseTenant(me, readStoredTenantId()) : null;
      setActiveTenantId(tenant);
      setStatus("authenticated");
    },
    [manager, setActiveTenantId],
  );

  const register = useCallback(
    async ({ email, password, fullName }: RegisterInput) => {
      const resp = await fetch(`${env.apiUrl}/v1/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, full_name: fullName }),
      });
      if (!resp.ok) {
        let code: string | undefined;
        let message = `Registration failed (${resp.status})`;
        try {
          const body = (await resp.json()) as {
            detail?: { code?: string; message?: string } | string;
          };
          if (typeof body.detail === "object" && body.detail !== null) {
            code = body.detail.code;
            if (body.detail.message) message = body.detail.message;
          } else if (typeof body.detail === "string") {
            message = body.detail;
          }
        } catch {
          /* keep default */
        }
        throw new AuthError(message, code, resp.status);
      }
      await signInWithPassword({ email, password });
    },
    [signInWithPassword],
  );

  const signOut = useCallback(async () => {
    // Clear local state first so the SPA can't get stuck "haunted" if the
    // Keycloak redirect fails (misconfigured post-logout URL, network, etc).
    setActiveTenantId(null);
    setUser(null);
    // Belt-and-suspenders: setActiveTenantId(null) above already clears the
    // query cache when a tenant was active, but if logout happens from an
    // anonymous-with-cached-data state we still want a clean slate.
    queryClient.clear();
    const signedOutUrl =
      typeof window !== "undefined"
        ? `${window.location.origin}/signed-out`
        : "/signed-out";
    if (!manager) {
      setStatus("anonymous");
      if (typeof window !== "undefined") {
        window.location.assign("/signed-out");
      }
      return;
    }
    try {
      await manager.removeUser();
    } catch {
      // best-effort
    }
    setStatus("anonymous");
    try {
      await manager.signoutRedirect({ post_logout_redirect_uri: signedOutUrl });
    } catch (err) {
      // If the IdP redirect fails, we're already locally signed-out. Land
      // the user on the signed-out page anyway so they get a clean exit.
      console.error("signoutRedirect failed", err);
      if (typeof window !== "undefined") {
        window.location.assign("/signed-out");
      }
    }
  }, [manager, queryClient, setActiveTenantId]);

  const getAccessToken = useCallback(async () => {
    if (!manager) return null;
    const u = await manager.getUser();
    if (!u) return null;
    if (u.expired) {
      try {
        const renewed = await manager.signinSilent();
        return renewed?.access_token ?? null;
      } catch {
        return null;
      }
    }
    return u.access_token;
  }, [manager]);

  const value = useMemo<AuthState>(
    () => ({
      status,
      user,
      manager,
      signIn,
      signInWithPassword,
      register,
      signOut,
      getAccessToken,
      devTenantId: activeTenantId,
      setActiveTenantId,
    }),
    [
      status,
      user,
      manager,
      signIn,
      signInWithPassword,
      register,
      signOut,
      getAccessToken,
      activeTenantId,
      setActiveTenantId,
    ],
  );

  return <AuthContext.Provider value={value}>{children(value)}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return ctx;
}
