import { cn } from "@/lib/cn";

export function MethodBadge({ method }: { method: string }) {
  const m = method.toLowerCase();
  return (
    <span className={cn("method", `method-${m}`)}>
      {method.toUpperCase()}
    </span>
  );
}
