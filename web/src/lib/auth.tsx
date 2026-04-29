import { User, UserManager, WebStorageStateStore } from "oidc-client-ts";
import {
  type ReactNode,
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

import { env } from "@/lib/env";

export interface AuthState {
  status: "loading" | "anonymous" | "authenticated";
  user: User | null;
  manager: UserManager;
  signIn: () => Promise<void>;
  signOut: () => Promise<void>;
  getAccessToken: () => Promise<string | null>;
}

const AuthContext = createContext<AuthState | null>(null);

function buildUserManager(): UserManager {
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

export function AuthProvider({ children }: AuthProviderProps) {
  const manager = useMemo(buildUserManager, []);
  const [user, setUser] = useState<User | null>(null);
  const [status, setStatus] = useState<AuthState["status"]>("loading");

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        // Handle a redirect-back if the URL contains the OIDC code.
        const search = window.location.search;
        if (search.includes("code=") && search.includes("state=")) {
          const u = await manager.signinRedirectCallback();
          if (!cancelled) {
            setUser(u);
            setStatus("authenticated");
            const target = (u.state as { returnTo?: string } | null)?.returnTo ?? "/";
            window.history.replaceState({}, "", target);
          }
          return;
        }
        const existing = await manager.getUser();
        if (existing && !existing.expired) {
          if (!cancelled) {
            setUser(existing);
            setStatus("authenticated");
          }
          return;
        }
        if (!cancelled) {
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
  }, [manager]);

  const signIn = useCallback(async () => {
    await manager.signinRedirect({
      state: { returnTo: window.location.pathname + window.location.search },
    });
  }, [manager]);

  const signOut = useCallback(async () => {
    await manager.signoutRedirect();
  }, [manager]);

  const getAccessToken = useCallback(async () => {
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
    () => ({ status, user, manager, signIn, signOut, getAccessToken }),
    [status, user, manager, signIn, signOut, getAccessToken],
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
