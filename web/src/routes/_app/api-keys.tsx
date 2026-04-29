import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";

import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/Card";
import { Field } from "@/components/ui/Field";
import { Input } from "@/components/ui/Input";
import { useApi } from "@/lib/useApi";
import type { IssuedApiKey } from "@/lib/api";

export const Route = createFileRoute("/_app/api-keys")({
  component: ApiKeysPage,
});

function ApiKeysPage() {
  const api = useApi();
  const qc = useQueryClient();
  const [name, setName] = useState("");
  const [issued, setIssued] = useState<IssuedApiKey | null>(null);

  const keys = useQuery({ queryKey: ["api-keys"], queryFn: () => api.listApiKeys() });

  const issue = useMutation({
    mutationFn: () => api.issueApiKey(name),
    onSuccess: (key) => {
      setIssued(key);
      setName("");
      void qc.invalidateQueries({ queryKey: ["api-keys"] });
    },
  });

  const revoke = useMutation({
    mutationFn: (id: string) => api.revokeApiKey(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["api-keys"] }),
  });

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-semibold text-slate-900">API Keys</h1>

      <Card>
        <CardHeader>
          <CardTitle>Issue a new key</CardTitle>
        </CardHeader>
        <CardBody className="flex items-end gap-3">
          <div className="flex-1">
            <Field label="Name" htmlFor="key-name" hint="A short label, e.g. agent-prod">
              <Input
                id="key-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="agent-prod"
              />
            </Field>
          </div>
          <Button
            disabled={!name.trim() || issue.isPending}
            onClick={() => issue.mutate()}
          >
            Issue
          </Button>
        </CardBody>
      </Card>

      {issued && (
        <Card className="border-amber-200 bg-amber-50">
          <CardHeader>
            <CardTitle>Save this token now — it won&apos;t be shown again</CardTitle>
          </CardHeader>
          <CardBody className="flex items-center justify-between gap-3">
            <code className="break-all rounded bg-white px-3 py-2 font-mono text-sm">
              {issued.token}
            </code>
            <Button variant="secondary" onClick={() => setIssued(null)}>
              Done
            </Button>
          </CardBody>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Active keys</CardTitle>
        </CardHeader>
        <CardBody className="p-0">
          {keys.data && keys.data.length === 0 && (
            <p className="p-4 text-sm text-slate-500">No keys yet.</p>
          )}
          {keys.data && keys.data.length > 0 && (
            <table className="w-full text-left text-sm">
              <thead className="border-b border-slate-100 text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-4 py-3">Name</th>
                  <th className="px-4 py-3">Prefix</th>
                  <th className="px-4 py-3">Last used</th>
                  <th className="px-4 py-3" />
                </tr>
              </thead>
              <tbody>
                {keys.data.map((k) => (
                  <tr key={k.id} className="border-b border-slate-100 last:border-0">
                    <td className="px-4 py-3 font-medium text-slate-900">{k.name}</td>
                    <td className="px-4 py-3 font-mono text-slate-700">{k.key_prefix}…</td>
                    <td className="px-4 py-3 text-slate-600">
                      {k.last_used_at ? new Date(k.last_used_at).toLocaleString() : "never"}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <Button
                        variant="danger"
                        size="sm"
                        onClick={() => revoke.mutate(k.id)}
                        disabled={revoke.isPending}
                      >
                        Revoke
                      </Button>
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
