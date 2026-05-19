import { useQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";

import { KpiCard } from "@/components/ui/KpiCard";
import { useApi } from "@/lib/useApi";

export const Route = createFileRoute("/_app/usage")({
  component: UsagePage,
});

function UsagePage() {
  const api = useApi();
  const usage = useQuery({
    queryKey: ["usage", "current"],
    queryFn: () => api.getCurrentUsage(),
    staleTime: 0,
    refetchOnWindowFocus: true,
  });
  const daily = useQuery({
    queryKey: ["usage", "daily", 30],
    queryFn: () => api.getDailyExecutions(30),
    staleTime: 0,
    refetchOnWindowFocus: true,
  });

  if (usage.isLoading) {
    return <div style={{ fontSize: 13, color: "var(--muted)" }}>Loading…</div>;
  }
  if (!usage.data) {
    return <div style={{ fontSize: 13, color: "var(--muted)" }}>No usage data.</div>;
  }

  const u = usage.data;
  const dailyPoints = daily.data?.points ?? [];
  const maxCount = dailyPoints.reduce((m, p) => Math.max(m, p.count), 0);
  const hasAnyExecutions = maxCount > 0;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
      <div className="responsive-grid-3" style={{ gap: 12 }}>
        <KpiCard
          label="Executions this month"
          value={u.executions.toLocaleString()}
          sub={`of ${u.monthly_execution_quota.toLocaleString()} included`}
          trend={`${((u.executions / Math.max(u.monthly_execution_quota, 1)) * 100).toFixed(1)}% of quota`}
        />
        <KpiCard
          label="Searches this month"
          value={u.searches.toLocaleString()}
          sub="of 50,000 included"
          trend={`${((u.searches / 50000) * 100).toFixed(1)}% of quota`}
        />
        <KpiCard
          label="Embedding tokens"
          value={`${(u.embedding_tokens / 1_000_000).toFixed(2)}M`}
          sub="of 5.0M included"
          trend={`${((u.embedding_tokens / 5_000_000) * 100).toFixed(1)}% of quota`}
        />
      </div>

      <div className="card" style={{ padding: 16 }}>
        <div style={{ display: "flex", alignItems: "center", marginBottom: 14 }}>
          <h3 style={{ fontSize: 13, fontWeight: 500, margin: 0 }}>Current month</h3>
          <span className="badge badge-slate" style={{ marginLeft: 8 }}>
            {u.year_month}
          </span>
          <span
            style={{ marginLeft: "auto", fontSize: 11.5, color: "var(--muted)" }}
            className="mono"
          >
            resets next month
          </span>
        </div>
        <QuotaRow label="Executions" used={u.executions} cap={u.monthly_execution_quota} />
        <QuotaRow label="Searches" used={u.searches} cap={50000} />
        <QuotaRow label="Embedding tokens" used={u.embedding_tokens} cap={5000000} unit="tok" />
      </div>

      <div className="card">
        <div style={{ padding: "12px 16px", borderBottom: "1px solid var(--border)" }}>
          <h3 style={{ fontSize: 13, fontWeight: 500, margin: 0 }}>
            Daily executions — last 30 days
          </h3>
        </div>
        {daily.isLoading ? (
          <div style={{ padding: 16, fontSize: 12, color: "var(--muted)" }}>Loading…</div>
        ) : !hasAnyExecutions ? (
          <div
            style={{
              padding: "32px 16px",
              fontSize: 12,
              color: "var(--muted)",
              textAlign: "center",
            }}
          >
            No executions in the last 30 days.
          </div>
        ) : (
          <>
            <div
              style={{ padding: 16, height: 200, display: "flex", alignItems: "flex-end", gap: 3 }}
            >
              {dailyPoints.map((p) => {
                const pct = maxCount > 0 ? (p.count / maxCount) * 95 : 0;
                const isToday = p.date === dailyPoints[dailyPoints.length - 1]?.date;
                return (
                  <div
                    key={p.date}
                    title={`${p.date}: ${p.count}`}
                    style={{
                      flex: 1,
                      height: `${Math.max(p.count > 0 ? 2 : 0, pct)}%`,
                      background: isToday ? "var(--accent)" : "var(--ink-2)",
                      borderRadius: 2,
                      opacity: 0.85,
                    }}
                  />
                );
              })}
            </div>
            <div
              style={{
                padding: "0 16px 12px",
                display: "flex",
                justifyContent: "space-between",
                fontSize: 10.5,
                color: "var(--muted)",
              }}
              className="mono"
            >
              <span>{dailyPoints[0]?.date ?? ""}</span>
              <span>{dailyPoints[dailyPoints.length - 1]?.date ?? ""}</span>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function QuotaRow({
  label,
  used,
  cap,
  unit,
}: {
  label: string;
  used: number;
  cap: number;
  unit?: string;
}) {
  const pct = cap > 0 ? Math.min(100, (used / cap) * 100) : 0;
  const color = pct > 80 ? "var(--accent)" : pct > 60 ? "var(--amber)" : "var(--ink)";
  return (
    <div style={{ marginBottom: 10 }}>
      <div style={{ display: "flex", alignItems: "center", marginBottom: 4 }}>
        <span style={{ fontSize: 12 }}>{label}</span>
        <span className="mono" style={{ marginLeft: "auto", fontSize: 11, color: "var(--muted)" }}>
          {used.toLocaleString()}
          {unit ?? ""} / {cap.toLocaleString()}
          {unit ?? ""}
        </span>
      </div>
      <div style={{ height: 5, background: "var(--border)", borderRadius: 3, overflow: "hidden" }}>
        <div style={{ width: `${pct}%`, height: "100%", background: color }} />
      </div>
    </div>
  );
}
