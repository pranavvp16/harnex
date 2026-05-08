import type { ReactNode } from "react";

interface FieldProps {
  label: string;
  htmlFor?: string;
  hint?: string;
  error?: string;
  children: ReactNode;
}

export function Field({ label, htmlFor, hint, error, children }: FieldProps) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 5 }}>
      <label
        htmlFor={htmlFor}
        style={{ fontSize: 12.5, fontWeight: 500, color: "var(--slate)" }}
      >
        {label}
      </label>
      {children}
      {hint && !error && (
        <p style={{ fontSize: 11.5, color: "var(--muted)", margin: 0 }}>{hint}</p>
      )}
      {error && (
        <p style={{ fontSize: 11.5, color: "var(--red)", margin: 0 }}>{error}</p>
      )}
    </div>
  );
}
