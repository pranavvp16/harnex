// Sample data for Harnex console
const SampleConnections = [
  { id: "cn_4f2a", name: "github-main", connector: "github", connectorName: "GitHub", mode: "OpenAPI", auth: "OAuth", endpoints: 487, status: "ready", baseUrl: "https://api.github.com", lastIndexed: "2026-04-29 14:22", created: "2026-03-12" },
  { id: "cn_8b1c", name: "stripe-prod", connector: "stripe", connectorName: "Stripe", mode: "OpenAPI", auth: "Bearer", endpoints: 312, status: "ready", baseUrl: "https://api.stripe.com", lastIndexed: "2026-04-30 09:11", created: "2026-02-08" },
  { id: "cn_2e9d", name: "jenkins-ci", connector: "jenkins", connectorName: "Jenkins", mode: "Native", auth: "API Key", endpoints: 142, status: "indexing", baseUrl: "https://ci.harnex.internal", lastIndexed: "—", created: "2026-04-30" },
  { id: "cn_6a3f", name: "linear-eng", connector: "linear", connectorName: "Linear", mode: "OpenAPI", auth: "API Key", endpoints: 98, status: "ready", baseUrl: "https://api.linear.app", lastIndexed: "2026-04-30 08:02", created: "2026-03-22" },
  { id: "cn_1d7e", name: "datadog-obs", connector: "datadog", connectorName: "Datadog", mode: "OpenAPI", auth: "API Key", endpoints: 264, status: "ready", baseUrl: "https://api.datadoghq.com", lastIndexed: "2026-04-30 06:45", created: "2026-03-04" },
  { id: "cn_9c2b", name: "slack-alerts", connector: "slack", connectorName: "Slack", mode: "OpenAPI", auth: "OAuth", endpoints: 156, status: "ready", baseUrl: "https://slack.com/api", lastIndexed: "2026-04-29 22:18", created: "2026-02-19" },
  { id: "cn_3f8a", name: "internal-billing", connector: "openapi", connectorName: "OpenAPI URL", mode: "OpenAPI", auth: "Bearer", endpoints: 47, status: "error", baseUrl: "https://billing.internal/api", lastIndexed: "2026-04-28 11:33", created: "2026-04-15", lastError: "401 Unauthorized while fetching /openapi.json — token rejected by upstream" },
  { id: "cn_7e5c", name: "notion-docs", connector: "notion", connectorName: "Notion", mode: "OpenAPI", auth: "Bearer", endpoints: 38, status: "disabled", baseUrl: "https://api.notion.com/v1", lastIndexed: "2026-04-20 10:00", created: "2026-03-30" },
];

const SampleExecutions = [
  { id: "ex_x9k", when: "2026-04-30 14:32:11", op: "GET /repos/{owner}/{repo}/pulls", connector: "github", mode: "execute", status: "success", dur: 184 },
  { id: "ex_p2l", when: "2026-04-30 14:31:48", op: "POST /v1/charges", connector: "stripe", mode: "execute", status: "success", dur: 312 },
  { id: "ex_r4m", when: "2026-04-30 14:30:09", op: "GET /api/v1/issues", connector: "linear", mode: "execute", status: "success", dur: 96 },
  { id: "ex_k7n", when: "2026-04-30 14:28:55", op: "POST /api/v2/events", connector: "datadog", mode: "execute", status: "success", dur: 142 },
  { id: "ex_h3p", when: "2026-04-30 14:27:21", op: "GET /repos/{owner}/{repo}/issues", connector: "github", mode: "execute", status: "error", dur: 5012, error: "403 rate limit exceeded" },
  { id: "ex_s8q", when: "2026-04-30 14:25:03", op: "POST /chat.postMessage", connector: "slack", mode: "execute", status: "success", dur: 221 },
  { id: "ex_j5r", when: "2026-04-30 14:23:44", op: "DELETE /v1/customers/{id}", connector: "stripe", mode: "execute", status: "success", dur: 178 },
  { id: "ex_b2s", when: "2026-04-30 14:22:11", op: "GET /api/v1/teams", connector: "linear", mode: "execute", status: "success", dur: 87 },
  { id: "ex_t6u", when: "2026-04-30 14:20:55", op: "POST /job/{name}/build", connector: "jenkins", mode: "execute", status: "timeout", dur: 30000 },
  { id: "ex_v9w", when: "2026-04-30 14:18:32", op: "PATCH /repos/{owner}/{repo}/pulls/{pull_number}", connector: "github", mode: "execute", status: "success", dur: 243 },
  { id: "ex_y3x", when: "2026-04-30 14:17:01", op: "GET /api/v1/billing/invoices", connector: "openapi", mode: "execute", status: "error", dur: 1840, error: "500 internal" },
  { id: "ex_z1y", when: "2026-04-30 14:15:18", op: "POST /v1/payment_intents", connector: "stripe", mode: "execute", status: "success", dur: 296 },
];

const SampleApiKeys = [
  { id: "k1", name: "production-agent", prefix: "hx_live_R3kQ", lastUsed: "2026-04-30 14:31", created: "2026-02-08" },
  { id: "k2", name: "staging-runner", prefix: "hx_live_8FtNm", lastUsed: "2026-04-30 12:04", created: "2026-03-19" },
  { id: "k3", name: "ci-pipeline", prefix: "hx_live_KjP2x", lastUsed: "2026-04-29 22:18", created: "2026-04-02" },
  { id: "k4", name: "research-notebook", prefix: "hx_live_Lm9Vc", lastUsed: "2026-04-22 10:11", created: "2026-04-15" },
];

// Indexed operations for the search playground
const SampleOperations = [
  { method: "GET", path: "/repos/{owner}/{repo}/pulls", summary: "List pull requests for a repository", connector: "github", connectorName: "GitHub", opId: "pulls/list", score: 0.94 },
  { method: "GET", path: "/repos/{owner}/{repo}/pulls/{pull_number}", summary: "Get a single pull request by number", connector: "github", connectorName: "GitHub", opId: "pulls/get", score: 0.88 },
  { method: "POST", path: "/repos/{owner}/{repo}/pulls", summary: "Create a new pull request", connector: "github", connectorName: "GitHub", opId: "pulls/create", score: 0.82 },
  { method: "GET", path: "/repos/{owner}/{repo}/issues", summary: "List issues in a repository", connector: "github", connectorName: "GitHub", opId: "issues/list-for-repo", score: 0.71 },
  { method: "PATCH", path: "/repos/{owner}/{repo}/pulls/{pull_number}", summary: "Update a pull request", connector: "github", connectorName: "GitHub", opId: "pulls/update", score: 0.69 },
  { method: "GET", path: "/api/v1/issues", summary: "List issues across teams in Linear", connector: "linear", connectorName: "Linear", opId: "issues.list", score: 0.62 },
  { method: "GET", path: "/repos/{owner}/{repo}/pulls/{pull_number}/files", summary: "List files changed in a pull request", connector: "github", connectorName: "GitHub", opId: "pulls/list-files", score: 0.58 },
];

window.SampleConnections = SampleConnections;
window.SampleExecutions = SampleExecutions;
window.SampleApiKeys = SampleApiKeys;
window.SampleOperations = SampleOperations;
