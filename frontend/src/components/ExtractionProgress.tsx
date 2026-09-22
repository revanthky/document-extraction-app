export const EXTRACTION_STAGES = [
  "Preparing PDF...",
  "Rendering PDF pages...",
  "Sending document to Vision Model...",
  "Processing extraction...",
  "Validating results...",
] as const;

interface ExtractionProgressProps {
  currentStage: number;
}

export function ExtractionProgress({ currentStage }: ExtractionProgressProps) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <ul className="space-y-2">
        {EXTRACTION_STAGES.map((stage, index) => {
          const isDone = index < currentStage;
          const isActive = index === currentStage;
          return (
            <li
              key={stage}
              className={`flex items-center gap-2 text-sm ${
                isActive ? "font-medium text-slate-900" : isDone ? "text-emerald-600" : "text-slate-400"
              }`}
            >
              <span>{isDone ? "✓" : isActive ? "…" : "○"}</span>
              {stage}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
