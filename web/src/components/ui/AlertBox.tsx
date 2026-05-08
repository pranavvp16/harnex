import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

type AlertVariant = "info" | "amber" | "red" | "accent";

interface AlertBoxProps {
  variant?: AlertVariant;
  children: ReactNode;
  className?: string;
}

const VARIANT_CLASS: Record<AlertVariant, string> = {
  info: "alert-info",
  amber: "alert-amber",
  red: "alert-red",
  accent: "alert-accent",
};

export function AlertBox({ variant = "info", children, className }: AlertBoxProps) {
  return (
    <div className={cn("alert", VARIANT_CLASS[variant], className)}>
      {children}
    </div>
  );
}
