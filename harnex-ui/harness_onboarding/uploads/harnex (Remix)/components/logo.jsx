// Harnex Logo + Icon — two directions
// A: "Bracket-H" — angle brackets forming an H monogram (code/dev metaphor)
// B: "Routing-H" — H monogram from routed/connected paths (orchestration metaphor)

const Logo = ({ variant = "A", size = 22, color = "currentColor", accent = "var(--accent)" }) => {
  if (variant === "A") {
    // Bracket-H: < | > forming an H, accent dot at center as the connector
    return (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
        <path d="M5 4 L2 12 L5 20" stroke={color} strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
        <path d="M19 4 L22 12 L19 20" stroke={color} strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
        <line x1="7.5" y1="12" x2="16.5" y2="12" stroke={color} strokeWidth="2.2" strokeLinecap="round"/>
        <circle cx="12" cy="12" r="2" fill={accent}/>
      </svg>
    );
  }
  // Routing-H: two vertical bars connected by a routed path (┐└) with accent node
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
      <line x1="4" y1="3.5" x2="4" y2="20.5" stroke={color} strokeWidth="2.2" strokeLinecap="round"/>
      <line x1="20" y1="3.5" x2="20" y2="20.5" stroke={color} strokeWidth="2.2" strokeLinecap="round"/>
      <path d="M4 12 H10 V8 H14 V16 H20" stroke={color} strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
      <circle cx="12" cy="12" r="2.2" fill={accent} stroke={color === "#fff" ? "transparent" : "transparent"} />
    </svg>
  );
};

const Wordmark = ({ variant = "A", size = 22, color = "currentColor", accent = "var(--accent)" }) => (
  <span style={{ display: "inline-flex", alignItems: "center", gap: 8, color }}>
    <Logo variant={variant} size={size} color={color} accent={accent} />
    <span style={{ fontFamily: "var(--font-sans)", fontWeight: 600, fontSize: size * 0.82, letterSpacing: "-0.02em", color }}>
      Harnex
    </span>
  </span>
);

window.Logo = Logo;
window.Wordmark = Wordmark;
