import { useQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";

import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/Card";
import { useApi } from "@/lib/useApi";

export const Route = createFileRoute("/_app/usage")({
  component: UsagePage,
});

function UsagePage() {
  const api = useApi();
  const usage = useQuery({
    queryKey: ["usage", "current"],
    queryFn: () => api.getCurrentUsage(),
  });

  if (usage.isLoading) return <p className="text-sm text-slate-500">Loading…</p>;
  if (!usage.data) return <p className="text-sm text-slate-500">No data.</p>;

  const u = usage.data;
  const pct = u.monthly_execution_quota
    ? Math.min(100, Math.round((u.executions / u.monthly_execution_quota) * 100))
    : 0;

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-semibold text-slate-900">Usage</h1>
      <Card>
        <CardHeader>
          <CardTitle>{u.year_month}</CardTitle>
        </CardHeader>
        <CardBody className="flex flex-col gap-4">
          <div>
            <div className="flex items-baseline justify-between">
              <span className="text-sm font-medium text-slate-700">Executions</span>
              <span className="font-mono text-sm text-slate-700">
                {u.executions} / {u.monthly_execution_quota}
              </span>
            </div>
            <div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-100">
              <div className="h-full bg-brand-600" style={{ width: `${pct}%` }} />
            </div>
          </div>
          <div className="flex items-baseline justify-between">
            <span className="text-sm font-medium text-slate-700">Searches</span>
            <span className="font-mono text-sm text-slate-700">{u.searches}</span>
          </div>
          <div className="flex items-baseline justify-between">
            <span className="text-sm font-medium text-slate-700">Embedding tokens</span>
            <span className="font-mono text-sm text-slate-700">{u.embedding_tokens}</span>
          </div>
        </CardBody>
      </Card>
    </div>
  );
}
