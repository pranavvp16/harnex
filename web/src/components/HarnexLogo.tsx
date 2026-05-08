interface HarnexLogoProps {
  size?: number;
  accent?: string;
  ink?: string;
  showWordmark?: boolean;
  dark?: boolean;
}

export function HarnexLogo({
  size = 24,
  accent = "var(--accent)",
  ink = "var(--ink)",
  showWordmark = true,
  dark = false,
}: HarnexLogoProps) {
  const inkC = dark ? "#FAFAF7" : ink;
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 8 }}>
      <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-label="Harnex">
        <path d="M5 4 H3 V20 H5" stroke={inkC} strokeWidth="2" strokeLinecap="square" fill="none" />
        <path d="M19 4 H21 V20 H19" stroke={inkC} strokeWidth="2" strokeLinecap="square" fill="none" />
        <rect x="7" y="11" width="10" height="2" fill={accent} />
        <circle cx="8" cy="12" r="1.6" fill={inkC} />
        <circle cx="16" cy="12" r="1.6" fill={inkC} />
      </svg>
      {showWordmark && (
        <span
          style={{
            fontFamily: "var(--font-sans)",
            fontWeight: 600,
            fontSize: size * 0.72,
            letterSpacing: "-0.02em",
            color: inkC,
          }}
        >
          Harnex
        </span>
      )}
    </span>
  );
}
