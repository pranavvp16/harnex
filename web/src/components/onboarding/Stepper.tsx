const LABELS = ["Profile", "Workspace", "Connection"];

export function Stepper({ step }: { step: number }) {
  if (step < 1) return null;
  return (
    <div className="ob-stepper">
      {LABELS.map((label, i) => {
        const idx = i + 1;
        const state = idx < step ? "done" : idx === step ? "current" : "todo";
        return (
          <div key={label} className={`ob-step ob-step-${state}`}>
            <div className="ob-step-bar" />
            <div className="ob-step-meta">
              <span className="mono ob-step-num">0{idx}</span>
              <span className="ob-step-label">{label}</span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
