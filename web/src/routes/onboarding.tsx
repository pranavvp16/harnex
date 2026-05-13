import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";

import type { MarkKey } from "@/components/onboarding/marks";
import { ConnectionStep } from "@/components/onboarding/ConnectionStep";
import { DoneStep } from "@/components/onboarding/DoneStep";
import {
  EmailRegisterStep,
  type EmailRegisterValue,
} from "@/components/onboarding/EmailRegisterStep";
import {
  EmailSignInStep,
  type EmailSignInValue,
} from "@/components/onboarding/EmailSignInStep";
import { OnboardingCanvas } from "@/components/onboarding/OnboardingCanvas";
import { OrgStep } from "@/components/onboarding/OrgStep";
import { ProfileStep } from "@/components/onboarding/ProfileStep";
import { SignInStep, type Provider } from "@/components/onboarding/SignInStep";
import { Stepper } from "@/components/onboarding/Stepper";
import type {
  ConnectionState,
  OrgState,
  ProfileState,
} from "@/components/onboarding/types";
import { HarnexLogo } from "@/components/HarnexLogo";
import { ApiError } from "@/lib/api";
import { AuthError, useAuth } from "@/lib/auth";
import { env } from "@/lib/env";
import { useApi } from "@/lib/useApi";

import "@/styles/onboarding.css";

export const Route = createFileRoute("/onboarding")({
  component: OnboardingPage,
});

const INITIAL_PROFILE: ProfileState = { fullName: "", handle: "" };
const INITIAL_ORG: OrgState = { orgName: "", teamSize: "2-10" };
const INITIAL_CONN: ConnectionState = { connection: null, displayName: "" };
const INITIAL_EMAIL_REG: EmailRegisterValue = { fullName: "", email: "", password: "" };
const INITIAL_EMAIL_SIGNIN: EmailSignInValue = { email: "", password: "" };

function OnboardingPage() {
  const auth = useAuth();
  const api = useApi();
  const navigate = useNavigate();

  const [step, setStep] = useState(0);
  // Tracks which inline form step 1 should render: signup (default) vs sign-in.
  // Toggled by the "Already have an account?" / "New to Harnex?" links.
  const [signInMode, setSignInMode] = useState(false);
  const [provider, setProvider] = useState<Provider | null>(null);
  const [profile, setProfile] = useState<ProfileState>(INITIAL_PROFILE);
  const [emailReg, setEmailReg] = useState<EmailRegisterValue>(INITIAL_EMAIL_REG);
  const [emailSignIn, setEmailSignIn] = useState<EmailSignInValue>(INITIAL_EMAIL_SIGNIN);
  const [org, setOrg] = useState<OrgState>(INITIAL_ORG);
  const [conn, setConn] = useState<ConnectionState>(INITIAL_CONN);
  const [connHover, setConnHover] = useState<MarkKey | null>(null);

  const [emailBusy, setEmailBusy] = useState(false);
  const [emailError, setEmailError] = useState<string | null>(null);
  const [signInBusy, setSignInBusy] = useState(false);
  const [signInError, setSignInError] = useState<string | null>(null);
  const [orgBusy, setOrgBusy] = useState(false);
  const [orgError, setOrgError] = useState<string | null>(null);
  // ConnectionStep is preference-only now; no async work happens on continue.
  const connBusy = false;
  const connError: string | null = null;
  const [createdSlug, setCreatedSlug] = useState<string>("");
  const [createdTenantId, setCreatedTenantId] = useState<string | null>(null);

  const next = () => setStep((s) => Math.min(4, s + 1));
  const back = () => setStep((s) => Math.max(0, s - 1));

  useEffect(() => {
    if (step !== 3) setConnHover(null);
  }, [step]);

  // Only fires once we know auth has settled. If the user lands on /onboarding
  // already authenticated (e.g. Google/GitHub callback), skip past SignInStep
  // and pre-fill profile from JWT claims. If they also already own a workspace,
  // bounce to /dashboard. Guard `step === 0` so we don't disrupt later steps.
  useEffect(() => {
    if (auth.status !== "authenticated") return;
    if (step !== 0) return;
    if (auth.devTenantId) {
      void navigate({ to: "/dashboard" });
      return;
    }
    const fullName = auth.user?.full_name ?? "";
    setProfile((prev) => (prev.fullName ? prev : { ...prev, fullName }));
    setStep(2);
  }, [auth.status, auth.devTenantId, auth.user, step, navigate]);

  const handleSignIn = async (p: Provider) => {
    setProvider(p);
    setSignInMode(false);
    if (p === "email") {
      // Show the inline email/password registration step within onboarding.
      next();
      return;
    }
    if (!env.devTenantId) {
      // Real auth build — broker straight to the chosen IDP via kc_idp_hint.
      // signIn triggers a top-level navigation; control won't return here.
      auth.signIn({ idpHint: p, returnTo: "/onboarding" });
      return;
    }
    // Dev / no-Keycloak path — fast-forward into the form.
    setProfile({ fullName: "", handle: "" });
    next();
  };

  const handleSwitchToSignIn = () => {
    setSignInError(null);
    setSignInMode(true);
    setStep(1);
  };

  const handleSwitchToSignUp = () => {
    setEmailError(null);
    setSignInMode(false);
    setProvider("email");
    setStep(1);
  };

  const handleEmailSignInContinue = async () => {
    setSignInError(null);
    setSignInBusy(true);
    try {
      await auth.signInWithPassword({
        email: emailSignIn.email.trim(),
        password: emailSignIn.password,
      });
      // Existing users skip onboarding entirely. If they somehow have no
      // workspace, the /_app guard will catch it and redirect them.
      void navigate({ to: "/dashboard" });
    } catch (err) {
      setSignInError(
        err instanceof AuthError ? err.message : "Sign-in failed. Please try again.",
      );
    } finally {
      setSignInBusy(false);
    }
  };

  const handleEmailRegisterContinue = async () => {
    setEmailError(null);
    setEmailBusy(true);
    try {
      await auth.register({
        email: emailReg.email.trim(),
        password: emailReg.password,
        fullName: emailReg.fullName.trim(),
      });
      // Carry the name forward so the workspace step can attribute the owner.
      setProfile({ fullName: emailReg.fullName.trim(), handle: "" });
      // Skip the separate Profile step — we already have the name.
      setStep(2);
    } catch (err) {
      setEmailError(
        err instanceof AuthError
          ? err.message
          : "Sign-up failed. Please try again.",
      );
    } finally {
      setEmailBusy(false);
    }
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
    // Onboarding only records the user's connector preference; we do NOT create
    // a Connection row here. Auto-creating a connection with auth_flow="none"
    // produces a half-configured row (indexable but not executable) that looks
    // identical to fully-configured ones in the UI — confusing and worthless.
    // The user finishes setup on /connections/new where credentials are required.
    next();
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
          {step === 0 && (
            <SignInStep
              onSignIn={handleSignIn}
              onSignInExisting={handleSwitchToSignIn}
            />
          )}
          {step === 1 &&
            (signInMode ? (
              <EmailSignInStep
                value={emailSignIn}
                onChange={setEmailSignIn}
                onContinue={() => void handleEmailSignInContinue()}
                onBack={back}
                onSwitchToSignUp={handleSwitchToSignUp}
                busy={signInBusy}
                serverError={signInError}
              />
            ) : provider === "email" ? (
              <EmailRegisterStep
                value={emailReg}
                onChange={setEmailReg}
                onContinue={() => void handleEmailRegisterContinue()}
                onBack={back}
                onSwitchToSignIn={handleSwitchToSignIn}
                busy={emailBusy}
                serverError={emailError}
              />
            ) : (
              <ProfileStep
                value={profile}
                onChange={setProfile}
                onContinue={next}
                onBack={back}
              />
            ))}
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
              previewConnector={connHover}
              onHoverConnectorChange={setConnHover}
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
        <OnboardingCanvas
          step={step}
          selectedConnector={conn.connection}
          previewConnector={connHover}
        />
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
