import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState } from "react";

import { ConnectionStep } from "@/components/onboarding/ConnectionStep";
import { DoneStep } from "@/components/onboarding/DoneStep";
import { OnboardingCanvas } from "@/components/onboarding/OnboardingCanvas";
import { OrgStep } from "@/components/onboarding/OrgStep";
import { ProfileStep } from "@/components/onboarding/ProfileStep";
import { SignInStep, type Provider } from "@/components/onboarding/SignInStep";
import { Stepper } from "@/components/onboarding/Stepper";
import { POPULAR_CONNECTIONS } from "@/components/onboarding/types";
import type {
  ConnectionState,
  OrgState,
  ProfileState,
} from "@/components/onboarding/types";
import { HarnexLogo } from "@/components/HarnexLogo";
import { ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { useApi } from "@/lib/useApi";

import "@/styles/onboarding.css";

export const Route = createFileRoute("/onboarding")({
  component: OnboardingPage,
});

const INITIAL_PROFILE: ProfileState = { fullName: "", handle: "" };
const INITIAL_ORG: OrgState = { orgName: "", teamSize: "2-10" };
const INITIAL_CONN: ConnectionState = { connection: null };

function OnboardingPage() {
  const auth = useAuth();
  const api = useApi();
  const navigate = useNavigate();

  const [step, setStep] = useState(0);
  const [provider, setProvider] = useState<Provider | null>(null);
  const [profile, setProfile] = useState<ProfileState>(INITIAL_PROFILE);
  const [org, setOrg] = useState<OrgState>(INITIAL_ORG);
  const [conn, setConn] = useState<ConnectionState>(INITIAL_CONN);

  const [orgBusy, setOrgBusy] = useState(false);
  const [orgError, setOrgError] = useState<string | null>(null);
  const [connBusy, setConnBusy] = useState(false);
  const [connError, setConnError] = useState<string | null>(null);
  const [createdSlug, setCreatedSlug] = useState<string>("");
  const [createdTenantId, setCreatedTenantId] = useState<string | null>(null);

  const next = () => setStep((s) => Math.min(4, s + 1));
  const back = () => setStep((s) => Math.max(0, s - 1));

  const handleSignIn = async (p: Provider) => {
    setProvider(p);
    if (auth.manager) {
      // Real Keycloak — kick off the redirect; flow resumes on callback.
      await auth.signIn();
      return;
    }
    // Dev / no-Keycloak path — fast-forward into the form.
    setProfile({ fullName: "", handle: p === "github" ? "" : "" });
    next();
  };

  const handleOrgContinue = async () => {
    setOrgError(null);
    setOrgBusy(true);
    try {
      const tenant = await api.createTenant({
        display_name: org.orgName.trim(),
        team_size: org.teamSize,
        profile: {
          full_name: profile.fullName.trim(),
          handle: profile.handle.trim() || null,
        },
      });
      auth.setActiveTenantId(tenant.id);
      setCreatedTenantId(tenant.id);
      setCreatedSlug(tenant.slug);
      next();
    } catch (err) {
      setOrgError(messageOf(err, "Could not create the workspace. Please try again."));
    } finally {
      setOrgBusy(false);
    }
  };

  const handleConnectionContinue = async () => {
    if (!conn.connection) {
      next();
      return;
    }
    setConnError(null);
    setConnBusy(true);
    try {
      const opt = POPULAR_CONNECTIONS.find((c) => c.key === conn.connection);
      const builtinKeys = new Set(["github"]);
      const isBuiltin = opt && builtinKeys.has(opt.key);
      await api.createConnection({
        name: opt?.name ?? "First connection",
        mode: isBuiltin ? "builtin" : "bare_url",
        connector_key: isBuiltin ? opt?.key ?? null : null,
        base_url: isBuiltin ? null : "https://example.com",
        auth_flow: "none",
      });
      next();
    } catch (err) {
      setConnError(messageOf(err, "Couldn't add that connector. You can add one from Connections later."));
    } finally {
      setConnBusy(false);
    }
  };

  const handleEnter = () => {
    void navigate({ to: "/dashboard" });
  };

  return (
    <div className="ob-root">
      <section className="ob-left">
        <header className="ob-header">
          <a className="ob-brand" href="#">
            <HarnexLogo size={22} />
          </a>
          <div className="ob-header-right">
            {step > 0 && step < 4 && (
              <span className="ob-progress mono">
                Step {step}
                <span className="ob-progress-sep">/</span>3
              </span>
            )}
            <a
              href="https://docs.harnex.dev"
              target="_blank"
              rel="noopener noreferrer"
              className="ob-help mono"
            >
              Need help?
            </a>
          </div>
        </header>

        <Stepper step={step} />

        <main className="ob-main">
          {step === 0 && <SignInStep onSignIn={handleSignIn} />}
          {step === 1 && (
            <ProfileStep
              value={profile}
              onChange={setProfile}
              onContinue={next}
              onBack={back}
            />
          )}
          {step === 2 && (
            <OrgStep
              value={org}
              onChange={setOrg}
              onContinue={() => void handleOrgContinue()}
              onBack={back}
              busy={orgBusy}
              serverError={orgError}
            />
          )}
          {step === 3 && (
            <ConnectionStep
              value={conn}
              onChange={setConn}
              onContinue={() => void handleConnectionContinue()}
              onBack={back}
              onSkip={next}
              busy={connBusy}
              serverError={connError}
            />
          )}
          {step === 4 && (
            <DoneStep
              profile={profile}
              org={org}
              connection={conn.connection}
              workspaceSlug={createdSlug}
              onEnter={handleEnter}
            />
          )}
        </main>

        <footer className="ob-footer mono">
          <span>© {new Date().getFullYear()} Harnex Labs</span>
          <span className="ob-footer-sep">·</span>
          <a href="https://status.harnex.dev" target="_blank" rel="noopener noreferrer">
            Status
          </a>
          <span className="ob-footer-sep">·</span>
          <a href="https://docs.harnex.dev" target="_blank" rel="noopener noreferrer">
            Docs
          </a>
          <span className="ob-footer-shard">
            {createdTenantId ? `tenant ${createdTenantId.slice(0, 8)}…` : "en — us-west-2"}
            {provider && ` · via ${provider}`}
          </span>
        </footer>
      </section>

      <aside className="ob-right" aria-hidden="true">
        <OnboardingCanvas step={step} selectedConnector={conn.connection} />
      </aside>
    </div>
  );
}

function messageOf(err: unknown, fallback: string): string {
  if (err instanceof ApiError) {
    const body = err.body as { message?: unknown; detail?: unknown } | null;
    const msg = body?.message ?? body?.detail;
    if (typeof msg === "string" && msg.trim().length > 0) return msg;
    return `${fallback} (status ${err.status})`;
  }
  if (err instanceof Error && err.message) return err.message;
  return fallback;
}
