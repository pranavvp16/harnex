import { forwardRef, type SelectHTMLAttributes } from "react";

import { cn } from "@/lib/cn";

export type SelectProps = SelectHTMLAttributes<HTMLSelectElement>;

export const Select = forwardRef<HTMLSelectElement, SelectProps>(function Select(
  { className, children, ...rest },
  ref,
) {
  return (
    <select
      ref={ref}
      className={cn(
        "focus-ring block w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900",
        className,
      )}
      {...rest}
    >
      {children}
    </select>
  );
});
