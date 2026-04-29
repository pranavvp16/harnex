import { useQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";

import { Card, CardBody } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { useApi } from "@/lib/useApi";

export const Route = createFileRoute("/_app/executions")({
  component: ExecutionsPage,
});

function ExecutionsPage() {
  const api = useApi();
  const executions = useQuery({
    queryKey: ["executions"],
    queryFn: () => api.listExecutions(100),
  });

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-semibold text-slate-900">Executions</h1>
      <Card>
        <CardBody className="p-0">
          {executions.isLoading && <p className="p-4 text-sm text-slate-500">Loading…</p>}
          {executions.data && executions.data.length === 0 && (
            <p className="p-4 text-sm text-slate-500">No executions yet.</p>
          )}
          {executions.data && executions.data.length > 0 && (
            <table className="w-full text-left text-sm">
              <thead className="border-b border-slate-100 text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-4 py-3">When</th>
                  <th className="px-4 py-3">Operation</th>
                  <th className="px-4 py-3">Mode</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Duration</th>
                </tr>
              </thead>
              <tbody>
                {executions.data.map((e) => (
                  <tr key={e.id} className="border-b border-slate-100 last:border-0">
                    <td className="px-4 py-3 text-slate-600">
                      {new Date(e.created_at).toLocaleString()}
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-slate-700">
                      {e.method && e.path ? `${e.method} ${e.path}` : e.operation_id ?? "—"}
                    </td>
                    <td className="px-4 py-3 text-slate-600">{e.mode}</td>
                    <td className="px-4 py-3">
                      <StatusBadge status={e.status} />
                    </td>
                    <td className="px-4 py-3 text-slate-600">
                      {e.duration_ms ? `${e.duration_ms} ms` : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </CardBody>
      </Card>
    </div>
  );
}
