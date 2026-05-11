import type { MarkKey } from "./marks";

import { wireLabelsForConnector } from "./types";

const HUB = { x: 420, y: 400 };

interface RingNode {
  key: string;
  deg: number;
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
  { key: "api-01", deg: 0 },
  { key: "api-02", deg: 45 },
  { key: "api-03", deg: 90 },
  { key: "api-04", deg: 135 },
  { key: "api-05", deg: 180 },
  { key: "api-06", deg: 225 },
  { key: "api-07", deg: 270 },
  { key: "api-08", deg: 315 },
];

const INNER: RingNode[] = [
  { key: "api-09", deg: 22 },
  { key: "api-10", deg: 112 },
  { key: "api-11", deg: 202 },
  { key: "api-12", deg: 292 },
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

export interface OnboardingCanvasProps {
  step: number;
  selectedConnector?: MarkKey | null;
  /** Step-3 grid hover — wins over selection for constellation API chips. */
  previewConnector?: MarkKey | null;
}

export function OnboardingCanvas({
  step,
  selectedConnector = null,
  previewConnector = null,
}: OnboardingCanvasProps) {
  const accentConnector = previewConnector ?? selectedConnector ?? null;
  const labelSource = wireLabelsForConnector(accentConnector);
  const labels = [...labelSource];
  const connectorStateAttr =
    selectedConnector != null ? "selected" : accentConnector != null ? "preview" : "none";

  const wires = NODE_LIST.map((n, i) => {
    const dx = HUB.x - n.x;
    const dy = HUB.y - n.y;
    const mx = (n.x + HUB.x) / 2;
    const my = (n.y + HUB.y) / 2;
    const perpX = -dy * 0.16;
    const perpY = dx * 0.16;
    const d = `M ${n.x} ${n.y} Q ${mx + perpX} ${my + perpY} ${HUB.x} ${HUB.y}`;
    const fadeStart = 2 + ((i * 11) % 24);
    const fadeMid = Math.min(fadeStart + 16 + (i % 4) * 5, 72);
    const fadeNearHub = 78 + (i % 4) * 3;
    return {
      key: n.key,
      d,
      x1: n.x,
      y1: n.y,
      x2: HUB.x,
      y2: HUB.y,
      staticGradientId: `oc-wire-static-${n.key}`,
      activeGradientId: `oc-wire-active-${n.key}`,
      fadeStart,
      fadeMid,
      fadeNearHub,
      delay: (i * 0.19) % 2.2,
      duration: 2.7 + (i % 4) * 0.28,
      label: labels[i % labels.length] ?? labels[0] ?? "",
    };
  });

  return (
    <div
      className="oc-stage"
      data-step={step}
      data-connector-state={connectorStateAttr}
    >
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
          {wires.map((w) => (
            <linearGradient
              key={w.staticGradientId}
              id={w.staticGradientId}
              gradientUnits="userSpaceOnUse"
              x1={w.x1}
              y1={w.y1}
              x2={w.x2}
              y2={w.y2}
            >
              <stop offset="0%" stopColor="var(--oc-wire-soft)" stopOpacity="0" />
              <stop offset={`${w.fadeStart}%`} stopColor="var(--oc-wire-soft)" stopOpacity="0" />
              <stop offset={`${w.fadeMid}%`} stopColor="var(--oc-wire-soft)" stopOpacity="0.13" />
              <stop offset={`${w.fadeNearHub}%`} stopColor="var(--oc-wire-soft)" stopOpacity="0.18" />
              <stop offset="100%" stopColor="var(--oc-wire-soft)" stopOpacity="0.26" />
            </linearGradient>
          ))}
          {wires.map((w) => (
            <linearGradient
              key={w.activeGradientId}
              id={w.activeGradientId}
              gradientUnits="userSpaceOnUse"
              x1={w.x1}
              y1={w.y1}
              x2={w.x2}
              y2={w.y2}
            >
              <stop offset="0%" stopColor="var(--oc-wire-hot)" stopOpacity="0" />
              <stop offset={`${w.fadeStart}%`} stopColor="var(--oc-wire-hot)" stopOpacity="0" />
              <stop offset={`${w.fadeMid}%`} stopColor="var(--oc-wire-hot)" stopOpacity="0.42" />
              <stop offset={`${w.fadeNearHub}%`} stopColor="var(--oc-wire-hot)" stopOpacity="0.68" />
              <stop offset="100%" stopColor="var(--oc-wire-hot)" stopOpacity="0.92" />
            </linearGradient>
          ))}
        </defs>

        <circle cx={HUB.x} cy={HUB.y} r="220" fill="url(#oc-hub-grad)" />

        <g className="oc-wire-base">
          {wires.map((w) => (
            <path
              key={`${w.key}-base`}
              className="oc-wire-static"
              d={w.d}
              style={{ stroke: `url(#${w.staticGradientId})` }}
            />
          ))}
        </g>

        <g className="oc-wires">
          {wires.map((w) => (
            <path
              key={w.key}
              className="oc-wire"
              d={w.d}
              style={{
                animationDelay: `${w.delay}s`,
                animationDuration: `${w.duration}s`,
                stroke: `url(#${w.activeGradientId})`,
              }}
            />
          ))}
        </g>

        {step >= 3 && (
          <g
            key={`labels-${accentConnector ?? "none"}-${step}`}
            className="oc-wire-labels"
          >
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
            style={{ animationDelay: "1.05s" }}
          />
          <circle
            cx={HUB.x}
            cy={HUB.y}
            r="60"
            className="oc-pulse-ring"
            style={{ animationDelay: "2.1s" }}
          />
        </g>

        <g className="oc-hub" transform={`translate(${HUB.x - 36} ${HUB.y - 36})`}>
          <circle cx="36" cy="36" r="38" className="oc-hub-ring" />
          <circle cx="36" cy="36" r="32" className="oc-hub-disc" />
          <g className="oc-hub-mark" transform="translate(12 12) scale(2)">
            <path
              d="M5 4 H3 V20 H5"
              className="oc-hub-mark-bracket"
              strokeWidth="2"
              strokeLinecap="square"
              fill="none"
            />
            <path
              d="M19 4 H21 V20 H19"
              className="oc-hub-mark-bracket"
              strokeWidth="2"
              strokeLinecap="square"
              fill="none"
            />
            <rect x="7" y="11" width="10" height="2" className="oc-hub-mark-accent" />
            <circle cx="8" cy="12" r="1.6" className="oc-hub-mark-dot" />
            <circle cx="16" cy="12" r="1.6" className="oc-hub-mark-dot" />
          </g>
        </g>

      </svg>

      <div className="oc-caption">
        <div className="oc-cap-kicker">
          {step >= 3 ? (
            <>
              LIVE WIRE · INGESTING <span style={{ color: "rgba(255,248,240,0.9)" }}>API</span>
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
