import type { HTMLAttributes, ReactNode } from "react";

import { cn } from "@/lib/cn";

export function Card({ className, style, ...rest }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("card", className)}
      style={style}
      {...rest}
    />
  );
}

export function CardHeader({ className, ...rest }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("flex items-center justify-between", className)}
      style={{ padding: "10px 16px", borderBottom: "1px solid var(--border)" }}
      {...rest}
    />
  );
}

export function CardTitle({ children }: { children: ReactNode }) {
  return (
    <h2 style={{ fontSize: 13, fontWeight: 500, margin: 0, color: "var(--ink)" }}>
      {children}
    </h2>
  );
}

export function CardBody({ className, style, ...rest }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={className}
      style={{ padding: 16, ...style }}
      {...rest}
    />
  );
}
