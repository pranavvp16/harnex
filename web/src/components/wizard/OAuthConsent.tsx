import type { ReactNode } from "react";

import { Ic } from "@/components/icons";

export type OAuthProviderKey = "GitHub" | "GitLab" | "Atlassian" | "Linear" | "Slack";

interface ProviderConfig {
  /** Display name shown in the heading. */
  label: string;
  /** Inline SVG mark. */
  mark: ReactNode;
  /** "We'll redirect you to <where>" for the lead text. */
  redirectTarget: string;
  /** Default scope set Harnex requests, in the provider's vocabulary. */
  scopes: { name: string; explanation: string }[];
  /** Plain-English summary of what Harnex can do with the granted access. */
  capabilitySummary: string[];
}

const PROVIDERS: Record<OAuthProviderKey, ProviderConfig> = {
  GitHub: {
    label: "GitHub",
    mark: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
        <path d="M12 .3a12 12 0 0 0-3.8 23.4c.6.1.8-.3.8-.6v-2.2c-3.3.7-4-1.4-4-1.4-.6-1.4-1.4-1.8-1.4-1.8-1.1-.7.1-.7.1-.7 1.2.1 1.9 1.2 1.9 1.2 1.1 1.9 2.9 1.4 3.6 1 .1-.8.4-1.4.7-1.7-2.6-.3-5.4-1.3-5.4-5.9 0-1.3.5-2.4 1.2-3.2-.1-.3-.5-1.5.1-3.2 0 0 1-.3 3.2 1.2.9-.3 1.9-.4 2.9-.4 1 0 2 .1 2.9.4 2.2-1.5 3.2-1.2 3.2-1.2.6 1.7.2 2.9.1 3.2.7.8 1.2 1.9 1.2 3.2 0 4.6-2.8 5.6-5.5 5.9.4.4.8 1.1.8 2.2v3.3c0 .3.2.7.8.6A12 12 0 0 0 12 .3" />
      </svg>
    ),
    redirectTarget: "github.com",
    scopes: [
      { name: "repo", explanation: "Read repository contents and metadata for connected repos" },
      { name: "read:org", explanation: "List organizations you belong to" },
      { name: "read:user", explanation: "Read your profile (username, email, avatar)" },
    ],
    capabilitySummary: [
      "List, search, and read repositories you grant access to",
      "Open and update issues / pull requests on those repos",
      "Cannot push to other users' repos or change org settings",
    ],
  },
  GitLab: {
    label: "GitLab",
    mark: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
        <path d="M12 21 3 13l1.5-5h2L8.5 13h7L17.5 8h2L21 13z" />
      </svg>
    ),
    redirectTarget: "gitlab.com",
    scopes: [
      { name: "read_api", explanation: "Read project, group, and pipeline data via the REST API" },
      { name: "read_repository", explanation: "Read repository contents on connected projects" },
      { name: "read_user", explanation: "Read your profile information" },
    ],
    capabilitySummary: [
      "Read projects, issues, and merge requests in selected groups",
      "Trigger pipelines if you grant write_repository explicitly later",
      "Cannot delete projects or modify protected branches",
    ],
  },
  Atlassian: {
    label: "Atlassian (Jira)",
    mark: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
        <path d="M12 4 L20 12 L16 16 L12 12 L8 16 L4 12 z" />
      </svg>
    ),
    redirectTarget: "atlassian.com",
    scopes: [
      { name: "read:jira-work", explanation: "Read issues, projects, and boards" },
      { name: "write:jira-work", explanation: "Create and update issues and comments" },
      { name: "read:jira-user", explanation: "Look up user profiles for assignment" },
    ],
    capabilitySummary: [
      "Read your Jira projects, issues, and sprints",
      "Create or update issues on your behalf",
      "Cannot manage workflows, schemes, or admin settings",
    ],
  },
  Linear: {
    label: "Linear",
    mark: (
      <svg
        width="18"
        height="18"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.6"
        aria-hidden
      >
        <circle cx="12" cy="12" r="8" />
        <path d="M6 12 L18 12 M6 8 L18 8 M6 16 L18 16" />
      </svg>
    ),
    redirectTarget: "linear.app",
    scopes: [
      { name: "read", explanation: "Read teams, cycles, projects, and issues" },
      { name: "write", explanation: "Create and update issues and comments" },
    ],
    capabilitySummary: [
      "Read all issues, projects, and cycles in your workspace",
      "Create or update issues on your behalf",
      "Cannot manage workspace billing or admin settings",
    ],
  },
  Slack: {
    label: "Slack",
    mark: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
        <rect x="4" y="10" width="6" height="2" rx="1" />
        <rect x="14" y="12" width="6" height="2" rx="1" />
        <rect x="10" y="4" width="2" height="6" rx="1" />
        <rect x="12" y="14" width="2" height="6" rx="1" />
      </svg>
    ),
    redirectTarget: "slack.com",
    scopes: [
      { name: "channels:read", explanation: "List public channels and their metadata" },
      { name: "chat:write", explanation: "Post messages as you in channels you join" },
      { name: "users:read", explanation: "Look up user profiles for mentions" },
    ],
    capabilitySummary: [
      "Read public channels you belong to",
      "Post messages on your behalf in channels you authorize",
      "Cannot read DMs unless you grant additional scopes later",
    ],
  },
};

interface Props {
  provider: OAuthProviderKey;
}

export function OAuthConsent({ provider }: Props) {
  const cfg = PROVIDERS[provider];
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: 12,
        padding: 14,
        borderRadius: "var(--r-lg)",
        border: "1px solid var(--accent-border)",
        background: "var(--accent-soft)",
        color: "var(--ink)",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <span
          aria-hidden
          style={{
            width: 32,
            height: 32,
            borderRadius: 6,
            background: "var(--surface)",
            border: "1px solid var(--accent-border)",
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            color: "var(--accent-ink)",
          }}
        >
          {cfg.mark}
        </span>
        <div style={{ display: "flex", flexDirection: "column" }}>
          <span style={{ fontSize: 13, fontWeight: 600, color: "var(--ink)" }}>
            Sign in with {cfg.label}
          </span>
          <span style={{ fontSize: 11.5, color: "var(--accent-ink)" }}>
            We&apos;ll redirect you to {cfg.redirectTarget} after creation.
          </span>
        </div>
      </div>

      <div>
        <div className="kicker" style={{ marginBottom: 6 }}>
          Requested scopes
        </div>
        <ul style={{ margin: 0, paddingLeft: 0, listStyle: "none", display: "flex", flexDirection: "column", gap: 6 }}>
          {cfg.scopes.map((scope) => (
            <li
              key={scope.name}
              style={{ display: "flex", alignItems: "flex-start", gap: 8, fontSize: 12 }}
            >
              <span className="badge badge-mono badge-accent" style={{ flexShrink: 0 }}>
                {scope.name}
              </span>
              <span style={{ color: "var(--ink-2)" }}>{scope.explanation}</span>
            </li>
          ))}
        </ul>
      </div>

      <div>
        <div className="kicker" style={{ marginBottom: 6 }}>
          What Harnex can do
        </div>
        <ul style={{ margin: 0, paddingLeft: 18, color: "var(--ink-2)", fontSize: 12, lineHeight: 1.55 }}>
          {cfg.capabilitySummary.map((line) => (
            <li key={line}>{line}</li>
          ))}
        </ul>
      </div>

      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 6,
          fontSize: 11,
          color: "var(--accent-ink)",
        }}
      >
        <span style={{ display: "inline-flex" }}>{Ic.lock}</span>
        Tokens stored encrypted in Infisical. Revoke at any time on the connection page.
      </div>
    </div>
  );
}
