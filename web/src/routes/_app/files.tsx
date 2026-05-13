import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { Download, FolderOpen, Trash2 } from "lucide-react";
import { useState } from "react";

import { Modal } from "@/components/ui/Modal";
import { useApi } from "@/lib/useApi";
import type { FileItem } from "@/lib/api";

export const Route = createFileRoute("/_app/files")({
  component: FilesPage,
});

const PAGE_SIZE = 50;
const SKILL_OPTIONS = [
  { value: "", label: "All skills" },
  { value: "pdf", label: "PDF" },
  { value: "docx", label: "Word" },
  { value: "xlsx", label: "Excel" },
  { value: "pptx", label: "PowerPoint" },
] as const;

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function FilesPage() {
  const api = useApi();
  const qc = useQueryClient();
  const [skillKey, setSkillKey] = useState<string>("");
  const [offset, setOffset] = useState(0);
  const [confirmDelete, setConfirmDelete] = useState<FileItem | null>(null);

  const files = useQuery({
    queryKey: ["files", { limit: PAGE_SIZE, offset, skillKey: skillKey || null }],
    queryFn: () =>
      api.listFiles({
        limit: PAGE_SIZE,
        offset,
        skillKey: skillKey || null,
      }),
  });

  const remove = useMutation({
    mutationFn: (id: string) => api.deleteFile(id),
    onSuccess: () => {
      setConfirmDelete(null);
      void qc.invalidateQueries({ queryKey: ["files"] });
    },
  });

  const items = files.data?.items ?? [];
  const total = files.data?.total ?? 0;
  const hasPrev = offset > 0;
  const hasNext = offset + PAGE_SIZE < total;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
      <div className="responsive-toolbar">
        <select
          className="select toolbar-control"
          style={{ width: 160 }}
          value={skillKey}
          onChange={(e) => {
            setSkillKey(e.target.value);
            setOffset(0);
          }}
        >
          {SKILL_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
        <span className="toolbar-spacer" />
        <span style={{ fontSize: 12, color: "var(--muted)" }}>
          {total === 0 ? "No files" : `${total} file${total === 1 ? "" : "s"}`}
        </span>
      </div>

      <div className="card table-scroll">
        <table className="tbl">
          <thead>
            <tr>
              <th>File</th>
              <th style={{ width: 100 }}>Skill</th>
              <th style={{ width: 100, textAlign: "right" }}>Size</th>
              <th style={{ width: 180 }}>Created</th>
              <th style={{ width: 140, textAlign: "right" }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {items.map((f) => (
              <tr key={f.id} className="row-hover">
                <td>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <FolderOpen size={14} color="var(--muted)" />
                    <span className="mono" style={{ fontSize: 12 }}>
                      {f.filename}
                    </span>
                  </div>
                </td>
                <td>
                  <span className="badge badge-slate">{f.skill_key || "—"}</span>
                </td>
                <td
                  className="mono"
                  style={{ fontSize: 11.5, color: "var(--muted)", textAlign: "right" }}
                >
                  {formatSize(f.size_bytes)}
                </td>
                <td className="mono" style={{ fontSize: 11.5, color: "var(--muted)" }}>
                  {new Date(f.created_at).toLocaleString()}
                </td>
                <td style={{ textAlign: "right" }}>
                  <a
                    className="btn btn-ghost btn-sm"
                    href={f.download_url}
                    download={f.filename}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{ gap: 4 }}
                  >
                    <Download size={12} />
                    Download
                  </a>
                  <button
                    className="btn btn-ghost btn-sm"
                    style={{ marginLeft: 4, color: "var(--red)", gap: 4 }}
                    onClick={() => setConfirmDelete(f)}
                    title="Delete file"
                  >
                    <Trash2 size={12} />
                  </button>
                </td>
              </tr>
            ))}
            {items.length === 0 && !files.isLoading && (
              <tr>
                <td
                  colSpan={5}
                  style={{ textAlign: "center", color: "var(--muted)", padding: 24 }}
                >
                  No files yet. Run the <span className="mono">execute</span> MCP tool with a{" "}
                  <span className="mono">skill_key</span> to generate one.
                </td>
              </tr>
            )}
            {files.isLoading && (
              <tr>
                <td
                  colSpan={5}
                  style={{ textAlign: "center", color: "var(--muted)", padding: 24 }}
                >
                  Loading…
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {(hasPrev || hasNext) && (
        <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
          <button
            className="btn btn-ghost btn-sm"
            disabled={!hasPrev}
            onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
          >
            Prev
          </button>
          <button
            className="btn btn-ghost btn-sm"
            disabled={!hasNext}
            onClick={() => setOffset(offset + PAGE_SIZE)}
          >
            Next
          </button>
        </div>
      )}

      <Modal
        open={confirmDelete !== null}
        title="Delete file?"
        confirmLabel="Delete"
        confirmVariant="danger"
        onConfirm={() => {
          if (confirmDelete) remove.mutate(confirmDelete.id);
        }}
        onCancel={() => setConfirmDelete(null)}
        pending={remove.isPending}
      >
        <p>
          This permanently removes{" "}
          <strong style={{ color: "var(--ink)" }}>{confirmDelete?.filename ?? "this file"}</strong>{" "}
          from object storage.
        </p>
        <p style={{ color: "var(--muted)", marginTop: 8 }}>
          The execution history is preserved, but the file itself cannot be recovered.
        </p>
      </Modal>
    </div>
  );
}
