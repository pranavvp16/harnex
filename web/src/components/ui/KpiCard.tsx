interface KpiCardProps {
  label: string;
  value: string | number;
  sub?: string;
  trend?: string;
  trendUp?: boolean;
}

export function KpiCard({ label, value, sub, trend, trendUp }: KpiCardProps) {
  return (
    <div className="card" style={{ padding: "14px 16px" }}>
      <div style={{ fontSize: 11.5, color: "var(--muted)", fontWeight: 500, marginBottom: 6 }}>
        {label}
      </div>
      <div
        style={{
          fontSize: 28,
          fontWeight: 600,
          letterSpacing: "-0.03em",
          color: "var(--ink)",
          lineHeight: 1.1,
        }}
      >
        {value}
      </div>
      {sub && (
        <div style={{ fontSize: 12, color: "var(--muted)", marginTop: 4 }}>{sub}</div>
      )}
      {trend && (
        <div
          style={{
            fontSize: 11.5,
            marginTop: 6,
            color: trendUp ? "var(--green)" : "var(--muted)",
            fontWeight: 500,
          }}
        >
          {trend}
        </div>
      )}
    </div>
  );
}
