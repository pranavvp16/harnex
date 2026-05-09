import { Link, createFileRoute } from "@tanstack/react-router";
import { useEffect, useMemo, useState } from "react";

import { HarnexLogo } from "@/components/HarnexLogo";

import "@/styles/onboarding.css";
import "@/styles/signed-out.css";

type Reason = "manual" | "timeout" | "admin" | "security";

interface Search {
  reason?: Reason;
  email?: string;
  workspace?: string;
}

const REASON_LABEL: Record<Reason, string> = {
  manual: "Manual sign-out",
  timeout: "Session timed out",
  admin: "Signed out by admin",
  security: "Signed out for security",
};

export const Route = createFileRoute("/signed-out")({
  component: SignedOutPage,
  validateSearch: (search: Record<string, unknown>): Search => ({
    reason: (search.reason as Reason | undefined) ?? "manual",
    email: typeof search.email === "string" ? search.email : undefined,
    workspace:
      typeof search.workspace === "string" ? search.workspace : undefined,
  }),
});

function SignedOutPage() {
  const { reason = "manual", email, workspace } = Route.useSearch();

  const [stamp] = useState(() => new Date());
  const receiptId = useMemo(
    () =>
      "RX-" +
      Math.random().toString(36).slice(2, 6).toUpperCase() +
      "-" +
      Math.random().toString(36).slice(2, 5).toUpperCase(),
    [],
  );

  // Strip any URL params after first paint so the user can't deep-link
  // someone else's email/workspace into a screenshot of this screen.
  useEffect(() => {
    if (typeof window === "undefined") return;
    if (window.location.search.length === 0) return;
    window.history.replaceState({}, "", window.location.pathname);
  }, []);

  const userLabel = email ? email.split("@")[0] : "you";

  return (
    <div className="ob-root so-root">
      <section className="ob-left so-left">
        <header className="ob-header">
          <a className="ob-brand" href="/home" aria-label="Harnex">
            <HarnexLogo size={22} />
          </a>
          <div className="ob-header-right">
            <span className="badge badge-slate badge-mono so-reason-badge">
              <span className="so-reason-dot" />
              {REASON_LABEL[reason].toUpperCase()}
            </span>
          </div>
        </header>

        <main className="ob-main so-main">
          <div className="ob-step-body so-body">
            <div className="ob-kicker mono">SESSION ENDED</div>
            <h1 className="ob-title">
              You&apos;ve been{" "}
              <span className="serif-i">signed out.</span>
            </h1>
            <p className="ob-sub">
              We&apos;ve cleared your local session. Tokens have been removed
              from this browser; nothing about your workspace data has changed.
            </p>

            <div className="so-context">
              <div className="so-context-cell">
                <span className="so-context-label mono">USER</span>
                <span className="so-context-value">
                  {userLabel}
                  {email && <span className="so-context-email">· {email}</span>}
                </span>
              </div>
              <div className="so-context-cell">
                <span className="so-context-label mono">WORKSPACE</span>
                <span className="so-context-value">
                  {workspace ? (
                    <>
                      <span>workspace</span>
                      <span className="so-context-slug mono">{workspace}</span>
                    </>
                  ) : (
                    <span className="so-context-slug mono">—</span>
                  )}
                </span>
              </div>
            </div>

            <div className="so-receipt" role="group" aria-label="Session receipt">
              <div className="so-receipt-head">
                <span className="so-receipt-id-wrap">
                  <span className="so-receipt-rx mono">RX</span>
                  <span className="so-receipt-id mono">{receiptId}</span>
                </span>
                <span className="so-receipt-stamp mono">
                  {formatStamp(stamp)}
                </span>
              </div>

              <ul className="so-receipt-rows">
                <li>
                  <span className="so-row-icon" aria-hidden="true">
                    <CheckMark />
                  </span>
                  <span className="so-row-label">Local session ended</span>
                  <span className="so-row-meta mono">cleared</span>
                </li>
                <li>
                  <span className="so-row-icon" aria-hidden="true">
                    <CheckMark />
                  </span>
                  <span className="so-row-label">Access &amp; refresh tokens</span>
                  <span className="so-row-meta mono">removed</span>
                </li>
                <li>
                  <span className="so-row-icon" aria-hidden="true">
                    <CheckMark />
                  </span>
                  <span className="so-row-label">Active workspace pointer</span>
                  <span className="so-row-meta mono">forgotten</span>
                </li>
                <li>
                  <span className="so-row-icon" aria-hidden="true">
                    <Dot />
                  </span>
                  <span className="so-row-label">Workspace data on server</span>
                  <span className="so-row-meta mono">untouched</span>
                </li>
              </ul>

              <div className="so-receipt-foot">
                <div className="so-foot-cell">
                  <span className="so-foot-label mono">REASON</span>
                  <span className="so-foot-value">{REASON_LABEL[reason]}</span>
                </div>
                <div className="so-foot-cell">
                  <span className="so-foot-label mono">DEVICE</span>
                  <span className="so-foot-value">{deviceLabel()}</span>
                </div>
                <div className="so-foot-cell">
                  <span className="so-foot-label mono">REGION</span>
                  <span className="so-foot-value">us-west-2</span>
                </div>
                <div className="so-foot-cell">
                  <span className="so-foot-label mono">REF</span>
                  <span className="so-foot-value mono">{receiptId.slice(-5)}</span>
                </div>
              </div>
            </div>

            <div className="so-actions">
              <Link to="/home" className="btn btn-accent btn-lg so-primary">
                Back to landing
                <span className="so-arrow" aria-hidden="true">→</span>
              </Link>
              <Link to="/onboarding" className="btn btn-secondary so-secondary">
                Sign in again
              </Link>
            </div>

            <SharedDeviceProtect />
          </div>
        </main>

        <footer className="ob-footer mono so-footer">
          <span>© {new Date().getFullYear()} Harnex Labs</span>
          <span className="ob-footer-sep">·</span>
          <a href="https://status.harnex.dev" target="_blank" rel="noopener noreferrer">
            Status
          </a>
          <span className="ob-footer-sep">·</span>
          <a href="https://docs.harnex.dev" target="_blank" rel="noopener noreferrer">
            Docs
          </a>
          <span className="ob-footer-shard">en — us-west-2</span>
        </footer>
      </section>

      <aside className="ob-right so-canvas-wrap" aria-hidden="true">
        <StandbyCanvas />
      </aside>
    </div>
  );
}

function SharedDeviceProtect() {
  const [confirming, setConfirming] = useState(false);
  const [done, setDone] = useState(false);

  const handleClear = () => {
    try {
      window.localStorage.clear();
      window.sessionStorage.clear();
    } catch {
      // best-effort — private mode etc.
    }
    setDone(true);
    setConfirming(false);
  };

  if (done) {
    return (
      <div className="so-protect">
        <span className="so-protect-icon" aria-hidden="true">
          <CheckMark />
        </span>
        <span className="so-protect-text">Browser storage cleared on this device.</span>
      </div>
    );
  }

  return (
    <div className={`so-protect${confirming ? " is-confirming" : ""}`}>
      <span className="so-protect-icon" aria-hidden="true">
        <ShieldGlyph />
      </span>
      <span className="so-protect-text">
        Sharing this computer?{" "}
        {confirming ? (
          <>
            This wipes any preferences cached in this browser.{" "}
            <button
              type="button"
              className="so-protect-link so-confirm"
              onClick={handleClear}
            >
              Yes, clear it
            </button>{" "}
            <button
              type="button"
              className="so-protect-cancel"
              onClick={() => setConfirming(false)}
            >
              cancel
            </button>
          </>
        ) : (
          <button
            type="button"
            className="so-protect-link"
            onClick={() => setConfirming(true)}
          >
            Clear local browser storage
          </button>
        )}
      </span>
    </div>
  );
}

function StandbyCanvas() {
  return (
    <>
      <div className="so-glow" />
      <div className="so-standby-chip">
        <span className="so-standby-led" aria-hidden="true" />
        <span>STANDBY</span>
      </div>
      <svg className="so-stage" viewBox="0 0 600 600" preserveAspectRatio="xMidYMid meet">
        {/* Reference orbits */}
        <circle className="so-orbit" cx="300" cy="300" r="120" />
        <circle className="so-orbit" cx="300" cy="300" r="180" />
        <circle className="so-orbit" cx="300" cy="300" r="240" />

        {/* Wires from hub to outer nodes */}
        {NODES.map((n) => (
          <line key={`wire-${n.id}`} className="so-wire" x1="300" y1="300" x2={n.x} y2={n.y} />
        ))}

        {/* Outer nodes (small chips on the orbit) */}
        {NODES.map((n) => (
          <g key={`node-${n.id}`} transform={`translate(${n.x - 14},${n.y - 14})`}>
            <rect className="so-node-bg" width="28" height="28" rx="6" />
            <g
              className="so-node-mark"
              transform="translate(8,8)"
              fill="currentColor"
            >
              <circle cx="6" cy="6" r="2.5" />
            </g>
          </g>
        ))}

        {/* Hub padlock */}
        <circle className="so-hub-halo" cx="300" cy="300" r="56" />
        <circle className="so-hub-disc" cx="300" cy="300" r="40" />
        <g transform="translate(300, 300)">
          <path
            className="so-lock-shackle"
            d="M -10 -4 V -10 a 10 10 0 0 1 20 0 V -4"
          />
          <rect
            className="so-lock-body"
            x="-14"
            y="-4"
            width="28"
            height="20"
            rx="3"
          />
          <circle className="so-lock-keyhole" cx="0" cy="6" r="1.8" />
          <line
            className="so-lock-body"
            x1="0"
            y1="6"
            x2="0"
            y2="11"
          />
        </g>
      </svg>

      <div className="so-caption">
        <div className="so-cap-kicker mono">SECURE — STANDBY</div>
        <div className="so-cap-title">
          Connections{" "}
          <span className="serif-i">at rest.</span>
          {" "}Nothing is reachable while you&apos;re signed out.
        </div>
        <div className="so-cap-meta mono">
          <span className="so-cap-dot" />
          tokens cleared
          <span style={{ opacity: 0.4 }}>·</span>
          vault sealed
          <span style={{ opacity: 0.4 }}>·</span>
          local cache flushed
        </div>
      </div>
    </>
  );
}

const NODES: { id: string; x: number; y: number }[] = (() => {
  const cx = 300;
  const cy = 300;
  const r = 240;
  const count = 8;
  return Array.from({ length: count }, (_, i) => {
    const a = (i / count) * Math.PI * 2 - Math.PI / 2;
    return {
      id: `n${i}`,
      x: Math.round(cx + r * Math.cos(a)),
      y: Math.round(cy + r * Math.sin(a)),
    };
  });
})();

function CheckMark() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
      <path d="M5 13l4 4L19 7" />
    </svg>
  );
}

function Dot() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <circle cx="12" cy="12" r="3" />
    </svg>
  );
}

function ShieldGlyph() {
  return (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
    </svg>
  );
}

function formatStamp(d: Date): string {
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  const hh = String(d.getHours()).padStart(2, "0");
  const mi = String(d.getMinutes()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd} ${hh}:${mi}`;
}

function deviceLabel(): string {
  if (typeof navigator === "undefined") return "browser";
  const ua = navigator.userAgent;
  if (/Mac/.test(ua)) return "macOS · browser";
  if (/Windows/.test(ua)) return "Windows · browser";
  if (/Linux/.test(ua)) return "Linux · browser";
  return "browser";
}
