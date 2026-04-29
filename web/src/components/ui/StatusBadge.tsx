import { cn } from "@/lib/cn";

const STYLES: Record<string, string> = {
  ready: "bg-green-100 text-green-800",
  indexing: "bg-amber-100 text-amber-800",
  pending: "bg-slate-100 text-slate-700",
  error: "bg-red-100 text-red-800",
  disabled: "bg-slate-200 text-slate-600",
  success: "bg-green-100 text-green-800",
  timeout: "bg-amber-100 text-amber-800",
};

export function StatusBadge({ status }: { status: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium capitalize",
        STYLES[status] ?? "bg-slate-100 text-slate-700",
      )}
    >
      {status}
    </span>
  );
}
