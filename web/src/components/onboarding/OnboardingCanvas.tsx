import { cloneElement, useEffect, useState } from "react";

import { Marks, type MarkKey } from "./marks";

const HUB = { x: 420, y: 400 };
const BUBBLE_R = 30;

interface RingNode {
  key: MarkKey;
  deg: number;
  label: string;
}

interface PlacedNode extends RingNode {
  x: number;
  y: number;
  ring: "outer" | "inner";
}

const polar = (cx: number, cy: number, r: number, deg: number) => {
  const rad = ((deg - 90) * Math.PI) / 180;
  return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) };
};

const OUTER: RingNode[] = [
  { key: "openai", deg: 0, label: "OpenAI" },
  { key: "anthropic", deg: 45, label: "Anthropic" },
  { key: "stripe", deg: 90, label: "Stripe" },
  { key: "postgres", deg: 135, label: "Postgres" },
  { key: "vercel", deg: 180, label: "Vercel" },
  { key: "slack", deg: 225, label: "Slack" },
  { key: "github", deg: 270, label: "GitHub" },
  { key: "notion", deg: 315, label: "Notion" },
];

const INNER: RingNode[] = [
  { key: "supabase", deg: 22, label: "Supabase" },
  { key: "linear", deg: 112, label: "Linear" },
  { key: "aws", deg: 202, label: "AWS" },
  { key: "sentry", deg: 292, label: "Sentry" },
];

const NODE_LIST: PlacedNode[] = [
  ...OUTER.map((n): PlacedNode => {
    const p = polar(HUB.x, HUB.y, 320, n.deg);
    return { ...n, x: p.x, y: p.y, ring: "outer" };
  }),
  ...INNER.map((n): PlacedNode => {
    const p = polar(HUB.x, HUB.y, 170, n.deg);
    return { ...n, x: p.x, y: p.y, ring: "inner" };
  }),
];

const DEFAULT_LABELS: string[] = [
  "GET /v1/data",
  "POST /v1/event",
  "GET /v1/items",
  "PATCH /v1/item",
  "GET /health",
];

const LABEL_SETS: Record<string, string[]> = {
  github: ["GET /repos", "POST /issues", "GET /pulls", "PATCH /issue", "GET /commits", "POST /webhooks", "GET /branches"],
  stripe: ["POST /charges", "GET /customers", "POST /refunds", "GET /invoices", "POST /checkout", "GET /balance"],
  postgres: ["SELECT users", "INSERT order", "UPDATE acct", "DELETE log", "BEGIN tx", "INDEX scan"],
  openai: ["POST /chat", "GET /models", "POST /embed", "POST /image", "GET /usage"],
  anthropic: ["POST /messages", "GET /models", "POST /tool", "stream events"],
  slack: ["POST /chat.send", "GET /channels", "POST /files", "GET /users"],
};

const labelsFor = (key: string): string[] => LABEL_SETS[key] ?? DEFAULT_LABELS;

interface NodeBubbleProps {
  node: PlacedNode;
  floatDelay: number;
  floatDur: number;
}

function NodeBubble({ node, floatDelay, floatDur }: NodeBubbleProps) {
  const markEl = Marks[node.key];
  const showLabel = node.ring === "outer";
  return (
    <g
      className={`oc-node oc-node-${node.key} oc-node-${node.ring}`}
      style={{ animationDelay: `${floatDelay}s`, animationDuration: `${floatDur}s` }}
      transform={`translate(${node.x - BUBBLE_R} ${node.y - BUBBLE_R})`}
    >
      <circle cx={BUBBLE_R} cy={BUBBLE_R} r={BUBBLE_R + 8} className="oc-halo" />
      <circle cx={BUBBLE_R} cy={BUBBLE_R} r={BUBBLE_R - 2} className="oc-bubble" />
      <circle cx={BUBBLE_R} cy={BUBBLE_R} r={BUBBLE_R - 5} className="oc-bubble-inner" />
      <svg
        x={BUBBLE_R - 14}
        y={BUBBLE_R - 14}
        width="28"
        height="28"
        viewBox="0 0 24 24"
        overflow="visible"
        className="oc-mark"
      >
        {cloneElement(markEl, { width: 24, height: 24 })}
      </svg>
      {showLabel && (
        <text
          x={BUBBLE_R}
          y={BUBBLE_R * 2 + 22}
          textAnchor="middle"
          className="oc-node-label"
        >
          {node.label}
        </text>
      )}
    </g>
  );
}

const CYCLE_KEYS: MarkKey[] = ["github", "stripe", "openai", "postgres"];

export interface OnboardingCanvasProps {
  step: number;
  selectedConnector?: MarkKey | null;
}

export function OnboardingCanvas({ step, selectedConnector }: OnboardingCanvasProps) {
  const [cycleIdx, setCycleIdx] = useState(0);

  useEffect(() => {
    if (selectedConnector) return;
    const t = window.setInterval(() => setCycleIdx((i) => (i + 1) % CYCLE_KEYS.length), 5000);
    return () => window.clearInterval(t);
  }, [selectedConnector]);

  const activeKey: MarkKey = selectedConnector ?? CYCLE_KEYS[cycleIdx % CYCLE_KEYS.length] ?? "github";
  const labels = labelsFor(activeKey);

  const wires = NODE_LIST.map((n, i) => {
    const dx = HUB.x - n.x;
    const dy = HUB.y - n.y;
    const mx = (n.x + HUB.x) / 2;
    const my = (n.y + HUB.y) / 2;
    const perpX = -dy * 0.16;
    const perpY = dx * 0.16;
    const d = `M ${n.x} ${n.y} Q ${mx + perpX} ${my + perpY} ${HUB.x} ${HUB.y}`;
    return {
      key: n.key,
      d,
      delay: (i * 0.4) % 5,
      duration: 4 + (i % 3) * 0.5,
      floatDelay: (i * 0.35) % 3,
      floatDur: 4.5 + (i % 4),
      label: labels[i % labels.length] ?? labels[0] ?? "",
    };
  });

  return (
    <div className="oc-stage" data-step={step} data-connector={activeKey}>
      <div className="oc-glow" aria-hidden="true" />
      <div className="oc-grid" aria-hidden="true" />

      <svg
        className="oc-svg"
        viewBox="0 0 840 800"
        preserveAspectRatio="xMidYMid meet"
        aria-hidden="true"
      >
        <defs>
          <radialGradient id="oc-hub-grad" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="var(--accent)" stopOpacity="0.55" />
            <stop offset="55%" stopColor="var(--accent)" stopOpacity="0.10" />
            <stop offset="100%" stopColor="var(--accent)" stopOpacity="0" />
          </radialGradient>
        </defs>

        <circle cx={HUB.x} cy={HUB.y} r="220" fill="url(#oc-hub-grad)" />

        <g className="oc-wires">
          {wires.map((w) => (
            <path
              key={w.key}
              className="oc-wire"
              d={w.d}
              style={{ animationDelay: `${w.delay}s`, animationDuration: `${w.duration}s` }}
            />
          ))}
        </g>

        {step >= 3 && (
          <g key={`labels-${activeKey}-${step}`} className="oc-wire-labels">
            {wires.map((w) => {
              const text = w.label;
              const chipW = Math.max(64, text.length * 6.6 + 14);
              return (
                <g key={`${w.key}-lbl`} className="oc-wlabel">
                  <rect
                    x={-chipW / 2}
                    y={-9}
                    width={chipW}
                    height={18}
                    rx="3"
                    className="oc-wlabel-bg"
                  />
                  <text x="0" y="3" textAnchor="middle" className="oc-wlabel-text">
                    {text}
                  </text>
                  <animateMotion
                    dur={`${w.duration}s`}
                    repeatCount="indefinite"
                    begin={`${w.delay}s`}
                    rotate="0"
                    path={w.d}
                  />
                  <animate
                    attributeName="opacity"
                    values="0;1;1;0"
                    keyTimes="0;0.18;0.78;1"
                    dur={`${w.duration}s`}
                    repeatCount="indefinite"
                    begin={`${w.delay}s`}
                  />
                </g>
              );
            })}
          </g>
        )}

        <g className="oc-pulses">
          <circle
            cx={HUB.x}
            cy={HUB.y}
            r="60"
            className="oc-pulse-ring"
            style={{ animationDelay: "0s" }}
          />
          <circle
            cx={HUB.x}
            cy={HUB.y}
            r="60"
            className="oc-pulse-ring"
            style={{ animationDelay: "1.5s" }}
          />
          <circle
            cx={HUB.x}
            cy={HUB.y}
            r="60"
            className="oc-pulse-ring"
            style={{ animationDelay: "3s" }}
          />
        </g>

        <g className="oc-hub" transform={`translate(${HUB.x - 36} ${HUB.y - 36})`}>
          <circle cx="36" cy="36" r="38" className="oc-hub-ring" />
          <circle cx="36" cy="36" r="32" className="oc-hub-disc" />
          <g transform="translate(12 12) scale(2)">
            <path
              d="M5 4 H3 V20 H5"
              stroke="var(--ink)"
              strokeWidth="2"
              strokeLinecap="square"
              fill="none"
            />
            <path
              d="M19 4 H21 V20 H19"
              stroke="var(--ink)"
              strokeWidth="2"
              strokeLinecap="square"
              fill="none"
            />
            <rect x="7" y="11" width="10" height="2" fill="var(--accent)" />
            <circle cx="8" cy="12" r="1.6" fill="var(--ink)" />
            <circle cx="16" cy="12" r="1.6" fill="var(--ink)" />
          </g>
        </g>

        <g className="oc-nodes">
          {NODE_LIST.map((n, i) => {
            const w = wires[i];
            return (
              <NodeBubble
                key={n.key}
                node={n}
                floatDelay={w?.floatDelay ?? 0}
                floatDur={w?.floatDur ?? 5}
              />
            );
          })}
        </g>
      </svg>

      <div className="oc-caption">
        <div className="oc-cap-kicker">
          {step >= 3 ? (
            <>
              LIVE WIRE · INGESTING{" "}
              <span style={{ color: "rgba(255,248,240,0.9)" }}>{activeKey.toUpperCase()}</span>
            </>
          ) : (
            "ONE HARNESS · MANY APIS"
          )}
        </div>
        <div className="oc-cap-title">
          {step <= 0 && (
            <>
              One harness for <span className="serif-i">every</span> tool your agent reaches for.
            </>
          )}
          {step === 1 && (
            <>
              Each API gets a typed <span className="serif-i">surface.</span>
            </>
          )}
          {step === 2 && (
            <>
              Routes resolve. <span className="serif-i">Wires</span> light up.
            </>
          )}
          {step === 3 && (
            <>
              Pick one. <span className="serif-i">Or skip</span> — agents are flexible.
            </>
          )}
          {step >= 4 && (
            <>
              You&apos;re connected. <span className="serif-i">Welcome aboard.</span>
            </>
          )}
        </div>
        <div className="oc-cap-meta mono">
          <span className="oc-dot-live" /> 12 connectors · streaming live endpoints
        </div>
      </div>
    </div>
  );
}
