import { useQueryClient } from "@tanstack/react-query";
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

export interface AuthUser {
  sub: string;
  email: string | null;
  full_name: string | null;
}

export interface AuthState {
  status: "loading" | "anonymous" | "authenticated";
  user: AuthUser | null;
  signIn: (opts?: SignInOptions) => void;
  signInWithPassword: (creds: PasswordCredentials) => Promise<void>;
  register: (input: RegisterInput) => Promise<void>;
  signOut: () => Promise<void>;
  /** Active tenant id for dev-header mode (VITE_HARNEX_DEV_TENANT build). Ignored for API auth when cookie auth is enabled. */
  devTenantId: string | null;
  /** Persist the active tenant id (used after onboarding creates a workspace). */
  setActiveTenantId: (id: string | null) => void;
}

const AuthContext = createContext<AuthState | null>(null);

// In-memory CSRF token. The browser also has it in a (non-HttpOnly) cookie,
// but the SPA prefers the in-memory copy so requests still work cross-origin
// where the cookie isn't readable. Kept here (not in React state) so api.ts
// can grab it synchronously inside `fetch` initializers.
let csrfTokenInMemory: string | null = null;

export function getCsrfToken(): string | null {
  return csrfTokenInMemory;
}

function setCsrfToken(token: string | null): void {
  csrfTokenInMemory = token;
}

interface AuthProviderProps {
  children: (auth: AuthState) => ReactNode;
}

interface SessionMeResponse {
  sub: string;
  email: string | null;
  full_name: string | null;
  memberships: Array<{ id: string; tenant_id: string; role: string }>;
  csrf_token: string;
}

interface SessionPasswordResponse {
  ok: boolean;
  user: AuthUser;
  csrf_token: string;
}

function chooseTenant(
  memberships: SessionMeResponse["memberships"],
  prefer: string | null,
): string | null {
  const ids = memberships.map((m) => m.tenant_id);
  if (prefer && ids.includes(prefer)) return prefer;
  return ids[0] ?? null;
}

async function parseAuthErrorBody(resp: Response): Promise<AuthError> {
  let code: string | undefined;
  let message = `${resp.status}`;
  try {
    const body = (await resp.json()) as {
      detail?: { code?: string; message?: string } | string;
    };
    if (typeof body.detail === "object" && body.detail !== null) {
      code = body.detail.code;
      if (body.detail.message) message = body.detail.message;
      else if (code) message = code.replace(/_/g, " ");
    } else if (typeof body.detail === "string") {
      message = body.detail;
    }
  } catch {
    /* keep default */
  }
  return new AuthError(message, code, resp.status);
}

export function AuthProvider({ children }: AuthProviderProps) {
  const queryClient = useQueryClient();
  const [user, setUser] = useState<AuthUser | null>(null);
  const [activeTenantId, setActiveTenantIdState] = useState<string | null>(
    () => env.devTenantId ?? null,
  );
  const previousTenantId = useRef<string | null>(activeTenantId);
  // Dev-mode build with no real auth → authenticated from the start. Otherwise
  // start in "loading" while we hit /v1/session/me to see if a cookie exists.
  const [status, setStatus] = useState<AuthState["status"]>(() =>
    env.devTenantId ? "authenticated" : "loading",
  );

  const setActiveTenantId = useCallback(
    (id: string | null) => {
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
        // private mode can fail — non-fatal.
      }
    },
    [queryClient],
  );

  useEffect(() => {
    if (env.devTenantId) {
      // Dev build short-circuits OIDC entirely.
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const resp = await fetch(`${env.apiUrl}/v1/session/me`, {
          credentials: "include",
        });
        if (cancelled) return;
        if (!resp.ok) {
          setCsrfToken(null);
          setUser(null);
          setActiveTenantId(null);
          setStatus("anonymous");
          return;
        }
        const me = (await resp.json()) as SessionMeResponse;
        setCsrfToken(me.csrf_token);
        setUser({ sub: me.sub, email: me.email, full_name: me.full_name });
        setActiveTenantId(chooseTenant(me.memberships, readStoredTenantId()));
        setStatus("authenticated");
      } catch (err) {
        console.error("session bootstrap failed", err);
        if (!cancelled) {
          setCsrfToken(null);
          setUser(null);
          setStatus("anonymous");
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [setActiveTenantId]);

  const signIn = useCallback((opts: SignInOptions = {}) => {
    if (env.devTenantId) return;
    const returnTo =
      opts.returnTo ?? window.location.pathname + window.location.search;
    const params = new URLSearchParams({ return_to: returnTo });
    if (opts.idpHint) params.set("idp_hint", opts.idpHint);
    // Top-level navigation — Keycloak's /auth needs the browser, not a fetch.
    window.location.assign(`${env.apiUrl}/v1/session/login?${params.toString()}`);
  }, []);

  const signInWithPassword = useCallback(
    async ({ email, password }: PasswordCredentials) => {
      const resp = await fetch(`${env.apiUrl}/v1/session/password`, {
        method: "POST",
        credentials: "include",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      if (!resp.ok) throw await parseAuthErrorBody(resp);
      const data = (await resp.json()) as SessionPasswordResponse;
      setCsrfToken(data.csrf_token);
      setUser(data.user);
      // Pull memberships in a second hop so we hydrate the tenant id correctly.
      try {
        const meResp = await fetch(`${env.apiUrl}/v1/session/me`, {
          credentials: "include",
        });
        if (meResp.ok) {
          const me = (await meResp.json()) as SessionMeResponse;
          setActiveTenantId(chooseTenant(me.memberships, readStoredTenantId()));
        }
      } catch {
        /* non-fatal — the route guard will redirect to /onboarding if missing */
      }
      setStatus("authenticated");
    },
    [setActiveTenantId],
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
    setActiveTenantId(null);
    setUser(null);
    queryClient.clear();
    try {
      await fetch(`${env.apiUrl}/v1/session/logout`, {
        method: "POST",
        credentials: "include",
        headers: csrfTokenInMemory
          ? { "X-CSRF-Token": csrfTokenInMemory }
          : undefined,
      });
    } catch (err) {
      console.error("logout failed", err);
    }
    setCsrfToken(null);
    setStatus("anonymous");
    if (typeof window !== "undefined") {
      window.location.assign("/signed-out");
    }
  }, [queryClient, setActiveTenantId]);

  const value = useMemo<AuthState>(
    () => ({
      status,
      user,
      signIn,
      signInWithPassword,
      register,
      signOut,
      devTenantId: activeTenantId,
      setActiveTenantId,
    }),
    [
      status,
      user,
      signIn,
      signInWithPassword,
      register,
      signOut,
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
