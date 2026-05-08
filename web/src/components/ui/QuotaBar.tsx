interface QuotaBarProps {
  label: string;
  used: number;
  total: number;
}

export function QuotaBar({ label, used, total }: QuotaBarProps) {
  const pct = total > 0 ? Math.min(100, Math.round((used / total) * 100)) : 0;
  const barColor =
    pct >= 80 ? "var(--red)" : pct >= 60 ? "var(--amber)" : "var(--green)";

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 5 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
        <span style={{ fontSize: 12.5, fontWeight: 500, color: "var(--ink)" }}>{label}</span>
        <span className="mono" style={{ fontSize: 12, color: "var(--muted)" }}>
          {used.toLocaleString()} / {total.toLocaleString()}
        </span>
      </div>
      <div
        style={{
          height: 5,
          borderRadius: 99,
          background: "var(--border)",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            height: "100%",
            width: `${pct}%`,
            borderRadius: 99,
            background: barColor,
            transition: "width 400ms ease",
          }}
        />
      </div>
      <div style={{ fontSize: 11, color: "var(--muted)" }}>{pct}% used</div>
    </div>
  );
}
