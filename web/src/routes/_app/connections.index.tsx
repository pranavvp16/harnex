import { useQuery } from "@tanstack/react-query";
import { Link, createFileRoute } from "@tanstack/react-router";

import { Button } from "@/components/ui/Button";
import { Card, CardBody } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { useApi } from "@/lib/useApi";

export const Route = createFileRoute("/_app/connections/")({
  component: ConnectionsIndex,
});

function ConnectionsIndex() {
  const api = useApi();
  const connections = useQuery({
    queryKey: ["connections"],
    queryFn: () => api.listConnections(),
  });

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-slate-900">Connections</h1>
        <Link to="/connections/new">
          <Button>New connection</Button>
        </Link>
      </div>
      {connections.isLoading && <p className="text-sm text-slate-500">Loading…</p>}
      {connections.error && (
        <p className="text-sm text-red-600">Failed to load: {String(connections.error)}</p>
      )}
      {connections.data && connections.data.length === 0 && (
        <Card>
          <CardBody className="flex flex-col items-center gap-3 py-12 text-center">
            <p className="text-sm text-slate-600">No connections yet.</p>
            <Link to="/connections/new">
              <Button>Connect your first API</Button>
            </Link>
          </CardBody>
        </Card>
      )}
      {connections.data && connections.data.length > 0 && (
        <Card>
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-100 text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-4 py-3">Name</th>
                <th className="px-4 py-3">Connector</th>
                <th className="px-4 py-3">Mode</th>
                <th className="px-4 py-3">Endpoints</th>
                <th className="px-4 py-3">Status</th>
              </tr>
            </thead>
            <tbody>
              {connections.data.map((c) => (
                <tr key={c.id} className="border-b border-slate-100 last:border-0">
                  <td className="px-4 py-3 font-medium text-slate-900">{c.name}</td>
                  <td className="px-4 py-3 text-slate-700">{c.connector_key ?? "generic"}</td>
                  <td className="px-4 py-3 text-slate-600">{c.mode}</td>
                  <td className="px-4 py-3 text-slate-700">{c.endpoint_count}</td>
                  <td className="px-4 py-3">
                    <StatusBadge status={c.status} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}
