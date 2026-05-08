import { cn } from "@/lib/cn";

const COLOR_MAP: Record<string, string> = {
  ready: "badge-green",
  success: "badge-green",
  indexing: "badge-amber",
  pending: "badge-amber",
  timeout: "badge-amber",
  error: "badge-red",
  disabled: "badge-slate",
};

export function StatusBadge({ status }: { status: string }) {
  const colorClass = COLOR_MAP[status] ?? "badge-slate";
  return (
    <span className={cn("badge", colorClass)}>
      <span className="badge-dot" />
      {status}
    </span>
  );
}
