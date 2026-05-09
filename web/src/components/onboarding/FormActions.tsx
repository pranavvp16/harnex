interface FormActionsProps {
  onBack?: () => void;
  backLabel?: string;
  primary: string;
  secondary?: string;
  onSecondary?: () => void;
  onContinue?: () => void;
  disabled?: boolean;
  busy?: boolean;
  layout?: "split" | "single";
}

export function FormActions({
  onBack,
  backLabel,
  primary,
  secondary,
  onSecondary,
  onContinue,
  disabled,
  busy,
  layout = "split",
}: FormActionsProps) {
  return (
    <div className={`ob-actions ob-actions-${layout}`}>
      {onBack && (
        <button type="button" className="ob-back" onClick={onBack}>
          ← {backLabel ?? "Back"}
        </button>
      )}
      <div className="ob-actions-right">
        {secondary && (
          <button type="button" className="btn btn-ghost" onClick={onSecondary}>
            {secondary}
          </button>
        )}
        <button
          type={onContinue ? "button" : "submit"}
          onClick={onContinue}
          className="btn btn-accent btn-lg ob-primary"
          disabled={disabled || busy}
        >
          {busy ? "Working…" : primary}
        </button>
      </div>
    </div>
  );
}
