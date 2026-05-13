import { useState } from "react";
import { Check, Copy } from "lucide-react";

type ClientId = "claude-code" | "claude-desktop" | "cursor" | "curl";

interface Client {
  id: ClientId;
  label: string;
  language: "bash" | "json";
  build: (url: string, key: string) => string;
  hint?: string;
}

const CLIENTS: Client[] = [
  {
    id: "claude-code",
    label: "Claude Code",
    language: "bash",
    hint: "Run once in any project. The MCP server registers globally.",
    build: (url, key) =>
      `claude mcp add harnex --transport http ${url} \\\n  --header "Authorization: Bearer ${key}"`,
  },
  {
    id: "cursor",
    label: "Cursor",
    language: "json",
    hint: "Add to ~/.cursor/mcp.json, then restart Cursor.",
    build: (url, key) =>
      `{
  "mcpServers": {
    "harnex": {
      "url": "${url}",
      "headers": {
        "Authorization": "Bearer ${key}"
      }
    }
  }
}`,
  },
  {
    id: "claude-desktop",
    label: "Claude Desktop",
    language: "json",
    hint:
      "Add to claude_desktop_config.json (Settings → Developer → Edit Config), then restart.",
    build: (url, key) =>
      `{
  "mcpServers": {
    "harnex": {
      "command": "npx",
      "args": [
        "-y", "mcp-remote",
        "${url}",
        "--header", "Authorization: Bearer ${key}"
      ]
    }
  }
}`,
  },
  {
    id: "curl",
    label: "curl",
    language: "bash",
    hint: "Quick connectivity check — should print the MCP server's tool list.",
    build: (url, key) =>
      `curl -X POST ${url} \\\n  -H "Authorization: Bearer ${key}" \\\n  -H "Content-Type: application/json" \\\n  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'`,
  },
];

interface Props {
  apiUrl: string;
  apiKey: string;
  /** Compact = landing-page sizing; default = full size for the API-keys page. */
  compact?: boolean;
  /** Hide the title bar (e.g. when the parent provides its own kicker). */
  hideTitle?: boolean;
}

export function McpInstallSnippets({ apiUrl, apiKey, compact = false, hideTitle = false }: Props) {
  const [active, setActive] = useState<ClientId>("claude-code");
  const [copied, setCopied] = useState(false);

  const client = CLIENTS.find((c) => c.id === active) ?? CLIENTS[0]!;
  const snippet = client.build(apiUrl, apiKey);

  const copy = () => {
    void navigator.clipboard.writeText(snippet);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1600);
  };

  return (
    <div
      className="card"
      style={{ overflow: "hidden", background: "var(--surface)" }}
    >
      {!hideTitle && (
        <div
          style={{
            padding: compact ? "10px 14px" : "12px 16px",
            borderBottom: "1px solid var(--border)",
            background: "var(--surface-2)",
            display: "flex",
            alignItems: "center",
            gap: 10,
          }}
        >
          <span
            style={{
              fontSize: 11,
              color: "var(--muted)",
              textTransform: "uppercase",
              letterSpacing: "0.06em",
              fontWeight: 500,
            }}
          >
            Use this key
          </span>
          <span style={{ fontSize: 12, color: "var(--muted)" }}>·</span>
          <span className="mono" style={{ fontSize: 11.5, color: "var(--muted)" }}>
            {apiUrl}
          </span>
        </div>
      )}

      <div
        role="tablist"
        aria-label="MCP client"
        style={{
          display: "flex",
          gap: 4,
          padding: compact ? "8px 10px 0" : "10px 12px 0",
          borderBottom: "1px solid var(--border-soft)",
          flexWrap: "wrap",
        }}
      >
        {CLIENTS.map((c) => {
          const isActive = c.id === active;
          return (
            <button
              key={c.id}
              role="tab"
              aria-selected={isActive}
              onClick={() => setActive(c.id)}
              style={{
                appearance: "none",
                background: "transparent",
                border: "none",
                padding: "6px 10px 9px",
                fontSize: 12.5,
                fontWeight: 500,
                color: isActive ? "var(--ink)" : "var(--muted)",
                cursor: "pointer",
                borderBottom: `2px solid ${isActive ? "var(--accent)" : "transparent"}`,
                marginBottom: -1,
                fontFamily: "inherit",
              }}
            >
              {c.label}
            </button>
          );
        })}
      </div>

      <div style={{ position: "relative" }}>
        <pre
          style={{
            margin: 0,
            padding: compact ? "14px 16px" : "16px 18px",
            fontFamily: "var(--font-mono)",
            fontSize: compact ? 11.5 : 12.5,
            lineHeight: 1.6,
            color: "var(--ink)",
            background: "var(--surface-2)",
            overflowX: "auto",
            whiteSpace: "pre",
          }}
        >
          {snippet}
        </pre>
        <button
          type="button"
          onClick={copy}
          aria-label="Copy snippet"
          className="btn btn-secondary btn-sm"
          style={{ position: "absolute", top: 10, right: 10 }}
        >
          {copied ? <Check size={12} /> : <Copy size={12} />}
          {copied ? "Copied" : "Copy"}
        </button>
      </div>

      {client.hint && (
        <div
          style={{
            padding: "8px 16px 12px",
            fontSize: 11.5,
            color: "var(--muted)",
            borderTop: "1px solid var(--border-soft)",
            background: "var(--surface)",
          }}
        >
          {client.hint}
        </div>
      )}
    </div>
  );
}
