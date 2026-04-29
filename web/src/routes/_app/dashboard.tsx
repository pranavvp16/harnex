import { useQuery } from "@tanstack/react-query";
import { Link, createFileRoute } from "@tanstack/react-router";

import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/Card";
import { useApi } from "@/lib/useApi";

export const Route = createFileRoute("/_app/dashboard")({
  component: Dashboard,
});

function Dashboard() {
  const api = useApi();
  const connections = useQuery({
    queryKey: ["connections"],
    queryFn: () => api.listConnections(),
  });
  const usage = useQuery({
    queryKey: ["usage", "current"],
    queryFn: () => api.getCurrentUsage(),
  });

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-slate-900">Dashboard</h1>
        <Link to="/connections/new">
          <Button>Connect an API</Button>
        </Link>
      </div>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Connections</CardTitle>
          </CardHeader>
          <CardBody>
            <div className="text-3xl font-semibold text-slate-900">
              {connections.data?.length ?? "—"}
            </div>
          </CardBody>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Executions this month</CardTitle>
          </CardHeader>
          <CardBody>
            <div className="text-3xl font-semibold text-slate-900">
              {usage.data?.executions ?? "—"}
            </div>
            <div className="mt-1 text-xs text-slate-500">
              quota {usage.data?.monthly_execution_quota ?? "—"}
            </div>
          </CardBody>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Searches this month</CardTitle>
          </CardHeader>
          <CardBody>
            <div className="text-3xl font-semibold text-slate-900">
              {usage.data?.searches ?? "—"}
            </div>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
