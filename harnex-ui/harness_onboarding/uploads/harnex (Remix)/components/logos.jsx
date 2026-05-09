// Harnex logo + connector marks (all original SVG, monochrome, brand-safe)
// Each component takes a `size` prop (height in px). Marks are square viewBox 24x24.

const HarnexLogo = ({ size = 24, accent = "var(--accent)", ink = "var(--ink)", showWordmark = true, dark = false }) => {
  const inkC = dark ? "#FAFAF7" : ink;
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 8 }}>
      <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-label="Harnex">
        {/* Bracketed H mark — left + right brackets cradling a horizontal connector bar */}
        <path d="M5 4 H3 V20 H5" stroke={inkC} strokeWidth="2" strokeLinecap="square" fill="none"/>
        <path d="M19 4 H21 V20 H19" stroke={inkC} strokeWidth="2" strokeLinecap="square" fill="none"/>
        <rect x="7" y="11" width="10" height="2" fill={accent}/>
        <circle cx="8" cy="12" r="1.6" fill={inkC}/>
        <circle cx="16" cy="12" r="1.6" fill={inkC}/>
      </svg>
      {showWordmark && (
        <span style={{ fontFamily: "var(--font-sans)", fontWeight: 600, fontSize: size * 0.72, letterSpacing: "-0.02em", color: inkC }}>
          Harnex
        </span>
      )}
    </span>
  );
};

// Alt logo direction — "command-prompt H" — angled chevron + H stem
const HarnexLogoAlt = ({ size = 24, accent = "var(--accent)", ink = "var(--ink)", showWordmark = true, dark = false }) => {
  const inkC = dark ? "#FAFAF7" : ink;
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 8 }}>
      <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-label="Harnex">
        <path d="M3 6 L8 12 L3 18" stroke={inkC} strokeWidth="2.2" strokeLinecap="square" strokeLinejoin="miter" fill="none"/>
        <rect x="11" y="5" width="2" height="14" fill={inkC}/>
        <rect x="13" y="11" width="6" height="2" fill={accent}/>
        <rect x="19" y="5" width="2" height="14" fill={inkC}/>
      </svg>
      {showWordmark && (
        <span style={{ fontFamily: "var(--font-sans)", fontWeight: 600, fontSize: size * 0.72, letterSpacing: "-0.02em", color: inkC }}>
          Harnex
        </span>
      )}
    </span>
  );
};

// Generic monochrome connector mark builder
const Mark = ({ children, bg = "transparent", size = 22 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" style={{ display: "block" }}>
    {bg !== "transparent" && <rect width="24" height="24" rx="4" fill={bg}/>}
    {children}
  </svg>
);

// All marks render in a single ink color so the whole marquee feels cohesive.
const I = "currentColor";

const Marks = {
  github: <Mark><circle cx="12" cy="12" r="9" fill={I}/><path d="M12 6.5c-2.7 0-5 2.2-5 4.9 0 2.2 1.4 4 3.4 4.7.2 0 .3-.1.3-.2v-.9c-1.4.3-1.7-.6-1.7-.6-.2-.6-.5-.7-.5-.7-.5-.3.04-.3.04-.3.5 0 .8.5.8.5.5.8 1.2.6 1.5.4 0-.4.2-.6.4-.8-1.1-.1-2.3-.5-2.3-2.4 0-.5.2-1 .5-1.3-.05-.1-.2-.6.05-1.3 0 0 .4-.1 1.4.5.4-.1.8-.2 1.3-.2.4 0 .9.05 1.3.2 1-.7 1.4-.5 1.4-.5.3.7.1 1.2.05 1.3.3.3.5.8.5 1.3 0 1.9-1.2 2.3-2.3 2.4.2.2.4.5.4 1v1.5c0 .1.1.2.3.2C15.6 15.4 17 13.6 17 11.4c0-2.7-2.3-4.9-5-4.9z" fill="#fff"/></Mark>,
  gitlab: <Mark><path d="M12 21 3 13l1.5-5h2L8.5 13h7L17.5 8h2L21 13z" fill={I}/></Mark>,
  bitbucket: <Mark><path d="M4 5h16l-2.5 14h-11z" fill={I}/><rect x="10" y="9.5" width="4" height="5" fill="#fff"/></Mark>,
  azuredevops: <Mark><path d="M3 9 L8 4 L8 7 L19 6 L21 9 L21 16 L8 20 L8 17 L3 14 z" fill={I}/></Mark>,
  jenkins: <Mark><circle cx="12" cy="10" r="4" fill={I}/><path d="M9 14h6l1 6H8z" fill={I}/></Mark>,
  circleci: <Mark><circle cx="12" cy="12" r="8" stroke={I} strokeWidth="1.5" fill="none"/><circle cx="12" cy="12" r="3" fill={I}/></Mark>,
  ghactions: <Mark><circle cx="12" cy="12" r="8" stroke={I} strokeWidth="1.5" fill="none"/><path d="M9 9 L15 12 L9 15 z" fill={I}/></Mark>,
  gitlabci: <Mark><rect x="4" y="6" width="16" height="12" rx="2" fill={I}/><path d="M9 12l2 2 4-4" stroke="#fff" strokeWidth="1.5" fill="none"/></Mark>,
  buildkite: <Mark><path d="M4 7 12 4 12 12 4 9z M12 12 20 9 20 17 12 20z" fill={I}/></Mark>,
  travisci: <Mark><circle cx="12" cy="12" r="8" stroke={I} strokeWidth="1.5" fill="none"/><path d="M8 12c1-2 3-2 4 0s3 2 4 0" stroke={I} strokeWidth="1.5" fill="none"/></Mark>,
  teamcity: <Mark><rect x="4" y="4" width="16" height="16" rx="2" fill={I}/><path d="M8 12h3M12 8v8M16 8h-2v8" stroke="#fff" strokeWidth="1.5" fill="none"/></Mark>,
  argocd: <Mark><circle cx="12" cy="12" r="7" stroke={I} strokeWidth="1.5" fill="none"/><circle cx="12" cy="12" r="2.5" fill={I}/><path d="M12 5v3M12 16v3M5 12h3M16 12h3" stroke={I} strokeWidth="1.5"/></Mark>,
  spinnaker: <Mark><path d="M12 4 C8 8 8 16 12 20 C16 16 16 8 12 4z" fill={I}/></Mark>,
  jira: <Mark><path d="M12 4 L20 12 L16 16 L12 12 L8 16 L4 12 z" fill={I}/></Mark>,
  linear: <Mark><circle cx="12" cy="12" r="8" stroke={I} strokeWidth="1.5" fill="none"/><path d="M6 12 L18 12 M6 8 L18 8 M6 16 L18 16" stroke={I} strokeWidth="1.5"/></Mark>,
  asana: <Mark><circle cx="12" cy="7" r="3" fill={I}/><circle cx="7" cy="15" r="3" fill={I}/><circle cx="17" cy="15" r="3" fill={I}/></Mark>,
  trello: <Mark><rect x="4" y="4" width="16" height="16" rx="2" fill={I}/><rect x="6" y="6" width="4" height="9" fill="#fff"/><rect x="14" y="6" width="4" height="6" fill="#fff"/></Mark>,
  clickup: <Mark><path d="M5 14 L12 8 L19 14 M5 18 L12 12 L19 18" stroke={I} strokeWidth="1.8" fill="none"/></Mark>,
  notion: <Mark><rect x="5" y="4" width="14" height="16" rx="1" fill={I}/><path d="M9 8 L9 16 M9 8 L15 14 L15 8" stroke="#fff" strokeWidth="1.5" fill="none"/></Mark>,
  monday: <Mark><circle cx="6" cy="12" r="2.5" fill={I}/><circle cx="12" cy="12" r="2.5" fill={I}/><circle cx="18" cy="12" r="2.5" fill={I}/></Mark>,
  datadog: <Mark><path d="M5 18 C7 14 10 12 14 12 L19 8 L18 14 L14 16 C12 17 9 18 5 18z" fill={I}/></Mark>,
  newrelic: <Mark><path d="M4 18 L12 4 L20 18 z" fill="none" stroke={I} strokeWidth="1.8"/></Mark>,
  grafana: <Mark><circle cx="12" cy="12" r="3" fill={I}/><path d="M12 3 v3 M12 18 v3 M3 12 h3 M18 12 h3 M5 5 l2 2 M17 17 l2 2 M5 19 l2 -2 M17 7 l2 -2" stroke={I} strokeWidth="1.5"/></Mark>,
  prometheus: <Mark><circle cx="12" cy="12" r="7" fill={I}/><path d="M9 9 L15 9 M8 12 L16 12" stroke="#fff" strokeWidth="1.5"/><circle cx="12" cy="16" r="1.5" fill="#fff"/></Mark>,
  sentry: <Mark><path d="M12 4 L20 18 H15 A3 3 0 0 0 9 18 L12 12 L15 17 L17 17 L12 7 L7 17 H4 z" fill={I}/></Mark>,
  honeycomb: <Mark><path d="M12 4 L19 8 V16 L12 20 L5 16 V8 z" fill="none" stroke={I} strokeWidth="1.8"/></Mark>,
  bugsnag: <Mark><circle cx="12" cy="12" r="7" stroke={I} strokeWidth="1.8" fill="none"/><circle cx="12" cy="12" r="2" fill={I}/></Mark>,
  pagerduty: <Mark><rect x="6" y="4" width="8" height="12" fill={I}/><rect x="6" y="16" width="3" height="4" fill={I}/></Mark>,
  opsgenie: <Mark><path d="M12 4 L19 9 L16 19 H8 L5 9 z" fill={I}/></Mark>,
  aws: <Mark><path d="M4 14 C7 17 17 17 20 14" stroke={I} strokeWidth="1.8" fill="none"/><path d="M5 9 H8 V12 H5z M10 9 H13 V12 H10z M15 9 H18 V12 H15z" fill={I}/></Mark>,
  gcp: <Mark><circle cx="12" cy="12" r="7" fill="none" stroke={I} strokeWidth="1.5"/><path d="M9 12 L11 14 L15 10" stroke={I} strokeWidth="1.8" fill="none"/></Mark>,
  azure: <Mark><path d="M11 4 L20 20 H10 L13 14 L8 20 H4 z" fill={I}/></Mark>,
  cloudflare: <Mark><path d="M5 16 C5 12 8 11 11 12 C11 9 14 8 17 10 C20 10 21 14 19 16 z" fill={I}/></Mark>,
  vercel: <Mark><path d="M12 5 L21 19 H3 z" fill={I}/></Mark>,
  netlify: <Mark><path d="M5 5 L12 12 L19 5 L19 13 L12 20 L5 13 z" fill="none" stroke={I} strokeWidth="1.8"/></Mark>,
  heroku: <Mark><rect x="6" y="4" width="12" height="16" rx="1.5" stroke={I} strokeWidth="1.5" fill="none"/><path d="M9 9 V15 M9 12 C12 12 14 11 14 14 V15" stroke={I} strokeWidth="1.5" fill="none"/></Mark>,
  render: <Mark><circle cx="9" cy="12" r="3" fill={I}/><circle cx="16" cy="12" r="3" fill="none" stroke={I} strokeWidth="1.5"/></Mark>,
  railway: <Mark><rect x="4" y="9" width="16" height="3" fill={I}/><rect x="4" y="14" width="16" height="3" fill={I}/><circle cx="7" cy="18" r="1" fill={I}/><circle cx="17" cy="18" r="1" fill={I}/></Mark>,
  flyio: <Mark><path d="M4 18 L9 10 L13 14 L16 8 L20 18 z" fill={I}/></Mark>,
  kubernetes: <Mark><path d="M12 4 L19 8 L17 16 L12 20 L7 16 L5 8 z" fill="none" stroke={I} strokeWidth="1.5"/><circle cx="12" cy="12" r="2" fill={I}/></Mark>,
  docker: <Mark><rect x="5" y="11" width="3" height="3" fill={I}/><rect x="9" y="11" width="3" height="3" fill={I}/><rect x="13" y="11" width="3" height="3" fill={I}/><rect x="9" y="7" width="3" height="3" fill={I}/><path d="M4 14 C8 18 16 18 19 14 L20 13" stroke={I} strokeWidth="1.5" fill="none"/></Mark>,
  terraform: <Mark><path d="M5 5 L11 8 V14 L5 11 z M11 8 L17 5 V11 L11 14 z M11 14 L17 11 V17 L11 20 z M5 12 L11 15 V20 L5 17 z" fill={I}/></Mark>,
  pulumi: <Mark><circle cx="9" cy="9" r="3" fill={I}/><circle cx="15" cy="15" r="3" fill={I}/><circle cx="15" cy="9" r="2" fill="none" stroke={I} strokeWidth="1.5"/></Mark>,
  postgres: <Mark><ellipse cx="12" cy="8" rx="7" ry="2.5" fill={I}/><path d="M5 8 V16 C5 17.5 8 18.5 12 18.5 C16 18.5 19 17.5 19 16 V8" stroke={I} strokeWidth="1.5" fill="none"/><ellipse cx="12" cy="12" rx="7" ry="2.5" fill="none" stroke={I} strokeWidth="1.5"/></Mark>,
  mysql: <Mark><path d="M4 16 C8 12 14 16 18 8 M16 14 L20 14 L20 18" stroke={I} strokeWidth="1.8" fill="none"/></Mark>,
  mongodb: <Mark><path d="M12 4 C9 8 9 16 12 20 C15 16 15 8 12 4 z" fill={I}/><path d="M12 4 V20" stroke="#fff" strokeWidth="1"/></Mark>,
  redis: <Mark><ellipse cx="12" cy="7" rx="7" ry="2" fill={I}/><path d="M5 7 V11 C5 12 8 13 12 13 C16 13 19 12 19 11 V7" stroke={I} strokeWidth="1.5" fill="none"/><path d="M5 13 V17 C5 18 8 19 12 19 C16 19 19 18 19 17 V13" stroke={I} strokeWidth="1.5" fill="none"/></Mark>,
  snowflake: <Mark><path d="M12 4 V20 M4 12 H20 M6 6 L18 18 M18 6 L6 18" stroke={I} strokeWidth="1.5"/></Mark>,
  bigquery: <Mark><circle cx="11" cy="11" r="6" stroke={I} strokeWidth="1.8" fill="none"/><path d="M15 15 L20 20" stroke={I} strokeWidth="2"/></Mark>,
  databricks: <Mark><path d="M4 8 L12 12 L20 8 L12 4 z M4 13 L12 17 L20 13 M4 17 L12 21 L20 17" stroke={I} strokeWidth="1.5" fill="none"/></Mark>,
  supabase: <Mark><path d="M12 4 L4 14 H10 L8 20 L20 10 H14 L16 4 z" fill={I}/></Mark>,
  neon: <Mark><circle cx="12" cy="12" r="7" stroke={I} strokeWidth="1.5" fill="none"/><path d="M9 8 V16 L15 8 V16" stroke={I} strokeWidth="1.5" fill="none"/></Mark>,
  planetscale: <Mark><circle cx="12" cy="12" r="8" fill={I}/><path d="M8 12 H20 M12 4 V20" stroke="#fff" strokeWidth="1.2"/></Mark>,
  elasticsearch: <Mark><path d="M4 6 H20 V10 H4 z M8 11 H20 V15 H8 z M12 16 H20 V20 H12 z" fill={I}/></Mark>,
  slack: <Mark><rect x="4" y="10" width="6" height="2" rx="1" fill={I}/><rect x="14" y="12" width="6" height="2" rx="1" fill={I}/><rect x="10" y="4" width="2" height="6" rx="1" fill={I}/><rect x="12" y="14" width="2" height="6" rx="1" fill={I}/></Mark>,
  discord: <Mark><path d="M5 7 C8 5 16 5 19 7 L20 16 C18 18 14 19 14 19 L13 17 C12 17 12 17 11 17 L10 19 C10 19 6 18 4 16 z" fill={I}/><circle cx="9.5" cy="13" r="1.2" fill="#fff"/><circle cx="14.5" cy="13" r="1.2" fill="#fff"/></Mark>,
  msteams: <Mark><rect x="9" y="6" width="11" height="11" rx="1" fill={I}/><text x="14.5" y="14.5" textAnchor="middle" fontSize="8" fill="#fff" fontWeight="700">T</text><circle cx="6" cy="9" r="3" fill={I}/></Mark>,
  gmail: <Mark><path d="M4 7 L12 13 L20 7 V17 H4 z" fill="none" stroke={I} strokeWidth="1.8"/></Mark>,
  outlook: <Mark><circle cx="9" cy="12" r="5" fill="none" stroke={I} strokeWidth="1.8"/><circle cx="9" cy="12" r="2" fill={I}/><rect x="14" y="9" width="6" height="6" fill="none" stroke={I} strokeWidth="1.5"/></Mark>,
  twilio: <Mark><circle cx="12" cy="12" r="8" stroke={I} strokeWidth="1.5" fill="none"/><circle cx="9" cy="9" r="1.5" fill={I}/><circle cx="15" cy="9" r="1.5" fill={I}/><circle cx="9" cy="15" r="1.5" fill={I}/><circle cx="15" cy="15" r="1.5" fill={I}/></Mark>,
  sendgrid: <Mark><path d="M4 4 H12 V12 H4z M12 12 H20 V20 H12z" fill={I}/><path d="M12 4 H20 V12 H12z M4 12 H12 V20 H4z" fill="none" stroke={I} strokeWidth="1.2"/></Mark>,
  confluence: <Mark><path d="M4 16 C7 11 11 11 14 14 C16 16 18 16 20 14" stroke={I} strokeWidth="2" fill="none"/><path d="M4 10 C7 15 11 15 14 12 C16 10 18 10 20 12" stroke={I} strokeWidth="2" fill="none"/></Mark>,
  gdrive: <Mark><path d="M9 4 L15 4 L21 14 L18 19 L12 9 L6 19 L3 14 z" fill={I}/></Mark>,
  dropbox: <Mark><path d="M7 5 L4 8 L7 11 L12 8 z M17 5 L20 8 L17 11 L12 8 z M7 13 L4 16 L7 19 L12 16 z M17 13 L20 16 L17 19 L12 16 z" fill={I}/></Mark>,
  box: <Mark><rect x="5" y="6" width="14" height="12" stroke={I} strokeWidth="1.5" fill="none" rx="1"/><path d="M5 10 H19 M9 6 V18 M15 6 V18" stroke={I} strokeWidth="1"/></Mark>,
  readme: <Mark><rect x="4" y="6" width="16" height="12" rx="1" stroke={I} strokeWidth="1.5" fill="none"/><path d="M12 6 V18 M7 10 H10 M7 13 H10 M14 10 H17 M14 13 H17" stroke={I} strokeWidth="1.2"/></Mark>,
  gitbook: <Mark><circle cx="9" cy="14" r="2" fill={I}/><path d="M11 13 L20 8 M11 15 L20 20" stroke={I} strokeWidth="1.5" fill="none"/></Mark>,
  mintlify: <Mark><path d="M4 18 V8 L9 13 L14 8 V18 M14 8 L20 8" stroke={I} strokeWidth="1.8" fill="none"/></Mark>,
  openapi: <Mark><circle cx="12" cy="12" r="7" stroke={I} strokeWidth="1.5" fill="none"/><circle cx="12" cy="12" r="2" fill={I}/><path d="M5 12 H8 M16 12 H19" stroke={I} strokeWidth="1.5"/></Mark>,
  swagger: <Mark><circle cx="12" cy="12" r="8" fill={I}/><path d="M7 10 H17 M7 12 H14 M7 14 H17" stroke="#fff" strokeWidth="1.2"/></Mark>,
  stripe: <Mark><path d="M16 7 H8 C6 7 6 10 8 10 L14 12 C16 12.5 16 16 14 16 H7" stroke={I} strokeWidth="2" fill="none"/></Mark>,
  plaid: <Mark><rect x="5" y="5" width="14" height="14" rx="2" stroke={I} strokeWidth="1.5" fill="none"/><path d="M9 9 H15 V15 H9z" fill={I}/></Mark>,
  shopify: <Mark><path d="M8 5 L16 5 L18 20 L6 20 z" fill={I}/><path d="M10 8 C10 5 14 5 14 8" stroke="#fff" strokeWidth="1.5" fill="none"/></Mark>,
  hubspot: <Mark><circle cx="14" cy="14" r="4" stroke={I} strokeWidth="1.5" fill="none"/><circle cx="14" cy="6" r="1.8" fill={I}/><path d="M14 8 V10 M11 11 L8 14 M8 14 V18" stroke={I} strokeWidth="1.5"/></Mark>,
  salesforce: <Mark><ellipse cx="12" cy="13" rx="7" ry="4" fill={I}/><circle cx="9" cy="11" r="2.5" fill={I}/><circle cx="15" cy="11" r="2" fill={I}/></Mark>,
  zendesk: <Mark><path d="M4 6 L12 6 L4 16 z M12 18 C12 14 16 10 20 10 L20 18 z" fill={I}/></Mark>,
  intercom: <Mark><rect x="5" y="5" width="14" height="14" rx="2" fill={I}/><path d="M8 9 V14 M11 9 V15 M14 9 V15 M17 9 V14" stroke="#fff" strokeWidth="1.2"/></Mark>,
  openai: <Mark><circle cx="12" cy="12" r="8" stroke={I} strokeWidth="1.5" fill="none"/><path d="M12 6 L17 9 L17 15 L12 18 L7 15 L7 9 z" stroke={I} strokeWidth="1.2" fill="none"/></Mark>,
  anthropic: <Mark><path d="M9 5 L5 19 H8 L9 16 H13 L14 19 H17 L13 5 z M10 13 L11 9 L12 13 z" fill={I}/></Mark>,
  cohere: <Mark><circle cx="12" cy="12" r="8" stroke={I} strokeWidth="1.5" fill="none"/><circle cx="12" cy="12" r="3" fill={I}/></Mark>,
  langchain: <Mark><circle cx="8" cy="8" r="3" stroke={I} strokeWidth="1.5" fill="none"/><circle cx="16" cy="16" r="3" stroke={I} strokeWidth="1.5" fill="none"/><path d="M10 10 L14 14" stroke={I} strokeWidth="1.5"/></Mark>,
  llamaindex: <Mark><path d="M4 18 V12 C4 9 7 6 12 6 C17 6 20 9 20 12 V18 M9 14 H10 M14 14 H15" stroke={I} strokeWidth="1.5" fill="none"/></Mark>,
  pinecone: <Mark><path d="M12 4 L8 8 L12 6 L16 8 z M12 7 L9 11 L12 9 L15 11 z M12 10 L10 14 L12 12 L14 14 z M11 14 L13 14 L12 20 z" fill={I}/></Mark>,
  weaviate: <Mark><path d="M12 4 L19 8 V16 L12 20 L5 16 V8 z" fill={I}/><path d="M12 4 V20 M5 8 L19 16 M19 8 L5 16" stroke="#fff" strokeWidth="0.8"/></Mark>,
  chroma: <Mark><circle cx="9" cy="9" r="4" fill={I} opacity="0.7"/><circle cx="15" cy="9" r="4" fill={I} opacity="0.7"/><circle cx="12" cy="15" r="4" fill={I} opacity="0.7"/></Mark>,
};

const ConnectorCell = ({ name, mark, w = 168, h = 56 }) => (
  <div style={{
    display: "flex", alignItems: "center", gap: 10,
    height: h, minWidth: w, padding: "0 16px",
    border: "1px solid var(--border)", borderRadius: 8, background: "var(--surface)",
    color: "var(--slate)", flexShrink: 0
  }}>
    <span style={{ color: "var(--ink)", display: "inline-flex" }}>{mark}</span>
    <span style={{ fontSize: 13, fontWeight: 500, color: "var(--ink)" }}>{name}</span>
  </div>
);

window.HarnexLogo = HarnexLogo;
window.HarnexLogoAlt = HarnexLogoAlt;
window.Marks = Marks;
window.ConnectorCell = ConnectorCell;
