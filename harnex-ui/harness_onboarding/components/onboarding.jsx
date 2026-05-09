// Onboarding flow — split layout, 4 steps after sign-in.
// Steps: 0 sign-in -> 1 full name -> 2 organization -> 3 first connection (optional) -> 4 done.

const POPULAR_CONNECTIONS = [
  { key: "github",    name: "GitHub",        kind: "Source control" },
  { key: "openai",    name: "OpenAI",        kind: "LLM provider" },
  { key: "anthropic", name: "Anthropic",     kind: "LLM provider" },
  { key: "postgres",  name: "Postgres",      kind: "Database" },
  { key: "stripe",    name: "Stripe",        kind: "Payments" },
  { key: "slack",     name: "Slack",         kind: "Messaging" },
  { key: "linear",    name: "Linear",        kind: "Issue tracker" },
  { key: "supabase",  name: "Supabase",      kind: "Backend" },
];

// ——— Visual stepper across the top of the form ———
const Stepper = ({ step, total = 3 }) => {
  // Step 0 is sign-in (no progress shown). Steps 1..total are the labelled progression.
  if (step < 1) return null;
  const labels = ["Profile", "Workspace", "Connection"];
  return (
    <div className="ob-stepper">
      {labels.map((label, i) => {
        const idx = i + 1;
        const state = idx < step ? "done" : idx === step ? "current" : "todo";
        return (
          <div key={label} className={`ob-step ob-step-${state}`}>
            <div className="ob-step-bar"/>
            <div className="ob-step-meta">
              <span className="mono ob-step-num">0{idx}</span>
              <span className="ob-step-label">{label}</span>
            </div>
          </div>
        );
      })}
    </div>
  );
};

// ——— Sign-in step ———
const SignInStep = ({ onSignIn }) => {
  const [loadingProvider, setLoadingProvider] = React.useState(null);
  const trigger = (provider) => {
    setLoadingProvider(provider);
    setTimeout(() => onSignIn(provider), 700);
  };
  return (
    <div className="ob-step-body">
      <div className="ob-kicker">WELCOME</div>
      <h1 className="ob-title">
        Let's get your <span className="serif-i">harness</span> wired up.
      </h1>
      <p className="ob-sub">
        Sign in to provision a Harnex workspace. We'll set up your first connection together — it takes about a minute.
      </p>

      <div className="ob-providers">
        <button
          className={`ob-provider ${loadingProvider === "google" ? "is-loading" : ""}`}
          onClick={() => trigger("google")}
          disabled={!!loadingProvider}
        >
          <span className="ob-provider-mark">
            <svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true">
              <path fill="#4285F4" d="M21.6 12.2c0-.7-.06-1.4-.18-2H12v3.83h5.4a4.6 4.6 0 0 1-2 3.04v2.5h3.23c1.9-1.74 2.97-4.32 2.97-7.37z"/>
              <path fill="#34A853" d="M12 22c2.7 0 4.96-.9 6.62-2.43l-3.23-2.5c-.9.6-2.05.96-3.39.96-2.6 0-4.81-1.76-5.6-4.13H3.07v2.6A10 10 0 0 0 12 22z"/>
              <path fill="#FBBC05" d="M6.4 13.9a6 6 0 0 1 0-3.8V7.5H3.07a10 10 0 0 0 0 9z"/>
              <path fill="#EA4335" d="M12 5.96c1.47 0 2.78.5 3.82 1.5l2.86-2.86A10 10 0 0 0 3.07 7.5L6.4 10.1c.79-2.37 3-4.13 5.6-4.13z"/>
            </svg>
          </span>
          <span className="ob-provider-label">Continue with Google</span>
          {loadingProvider === "google" && <span className="ob-spinner"/>}
        </button>

        <button
          className={`ob-provider ${loadingProvider === "github" ? "is-loading" : ""}`}
          onClick={() => trigger("github")}
          disabled={!!loadingProvider}
        >
          <span className="ob-provider-mark" style={{ color: "var(--ink)" }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
              <path d="M12 2C6.5 2 2 6.6 2 12.2c0 4.5 2.87 8.3 6.85 9.65.5.1.68-.22.68-.49 0-.24-.01-.88-.01-1.72-2.78.62-3.37-1.36-3.37-1.36-.46-1.18-1.12-1.5-1.12-1.5-.92-.64.07-.62.07-.62 1.01.07 1.55 1.06 1.55 1.06.9 1.57 2.37 1.12 2.95.85.09-.66.35-1.12.64-1.38-2.22-.26-4.55-1.13-4.55-5.03 0-1.11.39-2.02 1.03-2.73-.1-.26-.45-1.3.1-2.7 0 0 .84-.27 2.75 1.04A9.4 9.4 0 0 1 12 6.96c.85 0 1.7.12 2.5.34 1.91-1.31 2.75-1.04 2.75-1.04.55 1.4.2 2.44.1 2.7.64.71 1.03 1.62 1.03 2.73 0 3.91-2.34 4.77-4.57 5.02.36.31.68.92.68 1.86 0 1.34-.01 2.42-.01 2.75 0 .27.18.6.69.49C19.13 20.5 22 16.7 22 12.2 22 6.6 17.5 2 12 2z"/>
            </svg>
          </span>
          <span className="ob-provider-label">Continue with GitHub</span>
          {loadingProvider === "github" && <span className="ob-spinner"/>}
        </button>
      </div>

      <div className="ob-fineprint">
        By continuing you agree to the <a href="#">Terms</a> and <a href="#">Privacy</a> policy. We never request scopes we don't use; you can revoke access from your provider at any time.
      </div>
    </div>
  );
};

// ——— Profile step ———
const ProfileStep = ({ value, onChange, onContinue, onBack }) => {
  const [touched, setTouched] = React.useState(false);
  const ok = value.fullName.trim().length >= 2;
  return (
    <div className="ob-step-body">
      <div className="ob-kicker mono">STEP 01 · PROFILE</div>
      <h1 className="ob-title">
        First, what should we <span className="serif-i">call you?</span>
      </h1>
      <p className="ob-sub">
        Your name appears on commits, audit logs, and shared playground sessions. You can change it later from Settings.
      </p>

      <form className="ob-form" onSubmit={(e) => { e.preventDefault(); setTouched(true); if (ok) onContinue(); }}>
        <label className="ob-field">
          <span className="ob-field-label">Full name</span>
          <input
            className="input ob-input"
            value={value.fullName}
            onChange={(e) => onChange({ ...value, fullName: e.target.value })}
            placeholder="e.g. Alex Reyes"
            autoFocus
            spellCheck="false"
          />
          {touched && !ok && <span className="ob-error">Please enter at least two characters.</span>}
        </label>

        <label className="ob-field">
          <span className="ob-field-label">
            Display handle <span className="ob-field-opt">optional</span>
          </span>
          <div className="ob-input-prefix">
            <span className="ob-prefix mono">@</span>
            <input
              className="input ob-input"
              value={value.handle}
              onChange={(e) => onChange({ ...value, handle: e.target.value.replace(/[^a-z0-9-]/gi, "").toLowerCase() })}
              placeholder="alex"
              spellCheck="false"
            />
          </div>
        </label>

        <FormActions
          onBack={onBack}
          backLabel="Back"
          primary="Continue"
          disabled={!ok}
        />
      </form>
    </div>
  );
};

// ——— Organization step ———
const OrgStep = ({ value, onChange, onContinue, onBack }) => {
  const [touched, setTouched] = React.useState(false);
  const slug = value.orgName.trim().toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
  const ok = value.orgName.trim().length >= 2;

  return (
    <div className="ob-step-body">
      <div className="ob-kicker mono">STEP 02 · WORKSPACE</div>
      <h1 className="ob-title">
        Name your <span className="serif-i">organization.</span>
      </h1>
      <p className="ob-sub">
        Workspaces hold your connections, API keys, and execution history. One per team, usually.
      </p>

      <form className="ob-form" onSubmit={(e) => { e.preventDefault(); setTouched(true); if (ok) onContinue(); }}>
        <label className="ob-field">
          <span className="ob-field-label">Organization name</span>
          <input
            className="input ob-input"
            value={value.orgName}
            onChange={(e) => onChange({ ...value, orgName: e.target.value })}
            placeholder="e.g. Acme AI Lab"
            autoFocus
            spellCheck="false"
          />
          <div className="ob-helper">
            <span className="mono ob-helper-pre">harnex.dev/</span>
            <span className="mono ob-helper-slug">{slug || "your-org"}</span>
            <span className="ob-helper-status">{slug && (<><span className="ob-dot ob-dot-ok"/> available</>)}</span>
          </div>
          {touched && !ok && <span className="ob-error">Choose a name with at least two characters.</span>}
        </label>

        <fieldset className="ob-field ob-fieldset">
          <legend className="ob-field-label">Team size</legend>
          <div className="ob-segments">
            {["Just me", "2–10", "11–50", "51+"].map(s => (
              <label key={s} className={`ob-segment ${value.teamSize === s ? "is-active" : ""}`}>
                <input
                  type="radio"
                  name="size"
                  value={s}
                  checked={value.teamSize === s}
                  onChange={() => onChange({ ...value, teamSize: s })}
                />
                <span>{s}</span>
              </label>
            ))}
          </div>
        </fieldset>

        <FormActions
          onBack={onBack}
          backLabel="Back"
          primary="Continue"
          disabled={!ok}
        />
      </form>
    </div>
  );
};

// ——— First connection step (optional) ———
const ConnectionStep = ({ value, onChange, onContinue, onBack, onSkip }) => {
  const [search, setSearch] = React.useState("");
  const filtered = POPULAR_CONNECTIONS.filter(c =>
    c.name.toLowerCase().includes(search.toLowerCase()) || c.kind.toLowerCase().includes(search.toLowerCase())
  );
  const selected = value.connection;

  return (
    <div className="ob-step-body">
      <div className="ob-kicker mono">STEP 03 · CONNECTION <span className="ob-kicker-opt">· OPTIONAL</span></div>
      <h1 className="ob-title">
        Add your <span className="serif-i">first</span> connection.
      </h1>
      <p className="ob-sub">
        Pick a tool your agents will reach for most. We'll generate typed handlers and a sandbox in your console — no keys required to explore.
      </p>

      <div className="ob-search">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
          <circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>
        </svg>
        <input
          className="input ob-input"
          placeholder="Search 80+ connectors…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      <div className="ob-conn-grid">
        {filtered.map(c => {
          const active = selected === c.key;
          return (
            <button
              key={c.key}
              type="button"
              className={`ob-conn ${active ? "is-active" : ""}`}
              onClick={() => onChange({ ...value, connection: active ? null : c.key })}
            >
              <span className="ob-conn-mark">{Marks[c.key]}</span>
              <span className="ob-conn-text">
                <span className="ob-conn-name">{c.name}</span>
                <span className="ob-conn-kind">{c.kind}</span>
              </span>
              <span className="ob-conn-check">
                {active && (
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M5 12l5 5L20 7"/>
                  </svg>
                )}
              </span>
            </button>
          );
        })}
        {filtered.length === 0 && (
          <div className="ob-conn-empty mono">No connector named "{search}". Try GitHub, Postgres, OpenAI…</div>
        )}
      </div>

      <FormActions
        onBack={onBack}
        backLabel="Back"
        primary={selected ? `Connect ${POPULAR_CONNECTIONS.find(c => c.key === selected)?.name}` : "Continue"}
        secondary="Skip for now"
        onSecondary={onSkip}
      />
    </div>
  );
};

// ——— Done step ———
const DoneStep = ({ profile, org, connection, onEnter }) => {
  const connName = POPULAR_CONNECTIONS.find(c => c.key === connection)?.name;
  return (
    <div className="ob-step-body ob-done">
      <div className="ob-kicker mono">READY</div>
      <h1 className="ob-title">
        You're <span className="serif-i">all set,</span> {profile.fullName.split(" ")[0]}.
      </h1>
      <p className="ob-sub">
        <span className="mono">{org.orgName}</span> is provisioned. Here's what we set up:
      </p>

      <ul className="ob-checklist">
        <li><CheckMark/> Workspace <span className="mono">harnex.dev/{org.orgName.toLowerCase().replace(/[^a-z0-9]+/g, "-")}</span></li>
        <li><CheckMark/> 3 sandbox API keys generated (read, write, admin)</li>
        <li>
          {connection
            ? <><CheckMark/> {connName} connector wired up · ready to test</>
            : <><CheckSkip/> No connection yet — add one from the Console</>
          }
        </li>
        <li><CheckMark/> Audit log started · webhook receiver live</li>
      </ul>

      <FormActions
        primary="Open the console →"
        onContinue={onEnter}
        layout="single"
      />

      <div className="ob-tip">
        <span className="mono ob-tip-kbd">⌘K</span>
        <span>Press anywhere in the console to jump to a connection or run a request.</span>
      </div>
    </div>
  );
};

// ——— Shared form actions ———
const FormActions = ({ onBack, backLabel, primary, secondary, onSecondary, onContinue, disabled, layout }) => (
  <div className={`ob-actions ob-actions-${layout || "split"}`}>
    {onBack && (
      <button type="button" className="btn btn-ghost ob-back" onClick={onBack}>
        ← {backLabel || "Back"}
      </button>
    )}
    <div className="ob-actions-right">
      {secondary && (
        <button type="button" className="btn btn-ghost" onClick={onSecondary}>
          {secondary}
        </button>
      )}
      <button
        type={onContinue ? "button" : "submit"}
        onClick={onContinue}
        className="btn btn-accent btn-lg ob-primary"
        disabled={disabled}
      >
        {primary}
      </button>
    </div>
  </div>
);

const CheckMark = () => (
  <span className="ob-check ob-check-ok">
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
      <path d="M5 12l5 5L20 7"/>
    </svg>
  </span>
);
const CheckSkip = () => (
  <span className="ob-check ob-check-skip">
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
      <path d="M5 12h14"/>
    </svg>
  </span>
);

// ——— Main page ———
const OnboardingPage = ({ tweaks, setTweak, initialStep = 0 }) => {
  const [step, setStep] = React.useState(initialStep); // 0 sign-in, 1 name, 2 org, 3 conn, 4 done
  const [provider, setProvider] = React.useState(null);
  const [profile, setProfile] = React.useState(initialStep > 0 ? { fullName: "Alex Reyes", handle: "alex" } : { fullName: "", handle: "" });
  const [org, setOrg] = React.useState(initialStep > 1 ? { orgName: "Acme AI Lab", teamSize: "2–10" } : { orgName: "", teamSize: "2–10" });
  const [conn, setConn] = React.useState({ connection: null });

  const next = () => setStep(s => Math.min(4, s + 1));
  const back = () => setStep(s => Math.max(0, s - 1));

  const handleSignIn = (p) => {
    setProvider(p);
    // Pre-fill name based on provider in a realistic way
    const seed = p === "google" ? { fullName: "Alex Reyes", handle: "alex" } : { fullName: "Alex Reyes", handle: "areyes" };
    setProfile(seed);
    next();
  };

  return (
    <div className="ob-root">
      {/* LEFT — form */}
      <section className="ob-left">
        <header className="ob-header">
          <a className="ob-brand" href="#">
            <HarnexLogo size={22} />
          </a>

          <div className="ob-header-right">
            {step > 0 && step < 4 && (
              <span className="ob-progress mono">
                Step {step}<span className="ob-progress-sep">/</span>3
              </span>
            )}
            <a href="#" className="ob-help mono">Need help?</a>
          </div>
        </header>

        <Stepper step={step} total={3}/>

        <main className="ob-main">
          {step === 0 && <SignInStep onSignIn={handleSignIn}/>}
          {step === 1 && <ProfileStep value={profile} onChange={setProfile} onContinue={next} onBack={back}/>}
          {step === 2 && <OrgStep value={org} onChange={setOrg} onContinue={next} onBack={back}/>}
          {step === 3 && <ConnectionStep value={conn} onChange={setConn} onContinue={next} onBack={back} onSkip={next}/>}
          {step === 4 && <DoneStep profile={profile} org={org} connection={conn.connection} onEnter={() => alert("Console would open here")}/>}
        </main>

        <footer className="ob-footer mono">
          <span>© 2026 Harnex Labs</span>
          <span className="ob-footer-sep">·</span>
          <a href="#">Status</a>
          <span className="ob-footer-sep">·</span>
          <a href="#">Docs</a>
          <span className="ob-footer-sep">·</span>
          <span className="ob-footer-shard">en — us-west-2</span>
        </footer>
      </section>

      {/* RIGHT — animation */}
      <aside className="ob-right" aria-hidden="true">
        <OnboardingCanvas step={step} selectedConnector={conn.connection}/>
      </aside>
    </div>
  );
};

window.OnboardingPage = OnboardingPage;
