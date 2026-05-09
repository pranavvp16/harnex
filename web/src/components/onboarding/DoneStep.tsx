import { FormActions } from "./FormActions";
import { POPULAR_CONNECTIONS, type ConnectionState, type OrgState, type ProfileState } from "./types";

interface DoneStepProps {
  profile: ProfileState;
  org: OrgState;
  connection: ConnectionState["connection"];
  workspaceSlug: string;
  onEnter: () => void;
}

export function DoneStep({ profile, org, connection, workspaceSlug, onEnter }: DoneStepProps) {
  const connName = connection
    ? POPULAR_CONNECTIONS.find((c) => c.key === connection)?.name
    : null;
  const firstName = profile.fullName.trim().split(" ")[0] || "there";

  return (
    <div className="ob-step-body ob-done">
      <div className="ob-kicker mono">READY</div>
      <h1 className="ob-title">
        You&apos;re <span className="serif-i">all set,</span> {firstName}.
      </h1>
      <p className="ob-sub">
        <span className="mono">{org.orgName}</span> is provisioned. Here&apos;s what we set up:
      </p>

      <ul className="ob-checklist">
        <li>
          <CheckMark />
          Workspace <span className="mono">harnex.dev/{workspaceSlug}</span>
        </li>
        <li>
          <CheckMark /> 3 sandbox API keys ready to issue
        </li>
        <li>
          {connName ? (
            <>
              <CheckMark /> {connName} connector wired up · ready to test
            </>
          ) : (
            <>
              <CheckSkip /> No connection yet — add one from the Console
            </>
          )}
        </li>
        <li>
          <CheckMark /> Audit log started · webhook receiver live
        </li>
      </ul>

      <FormActions primary="Open the console →" onContinue={onEnter} layout="single" />

      <div className="ob-tip">
        <span className="mono ob-tip-kbd">⌘K</span>
        <span>Press anywhere in the console to jump to a connection or run a request.</span>
      </div>
    </div>
  );
}

function CheckMark() {
  return (
    <span className="ob-check ob-check-ok">
      <svg
        width="12"
        height="12"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M5 12l5 5L20 7" />
      </svg>
    </span>
  );
}

function CheckSkip() {
  return (
    <span className="ob-check ob-check-skip">
      <svg
        width="12"
        height="12"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M5 12h14" />
      </svg>
    </span>
  );
}
