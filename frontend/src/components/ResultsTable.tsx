import { Fragment, useState } from "react";
import type { ExtractionResultItem } from "../types";

const LOW_CONFIDENCE_THRESHOLD = 0.7;

function formatValue(value: ExtractionResultItem["value"]): string {
  if (value === null || value === undefined) return "";
  return String(value);
}

export function ResultsTable({ results }: { results: ExtractionResultItem[] }) {
  const [expanded, setExpanded] = useState<string | null>(null);

  return (
    <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
      <table className="min-w-full divide-y divide-slate-200 text-sm">
        <thead className="bg-slate-50">
          <tr>
            <th className="px-4 py-2 text-left font-medium text-slate-600">Field</th>
            <th className="px-4 py-2 text-left font-medium text-slate-600">Value</th>
            <th className="px-4 py-2 text-left font-medium text-slate-600">Confidence</th>
            <th className="px-4 py-2 text-left font-medium text-slate-600">Page</th>
            <th className="px-4 py-2" />
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {results.map((item) => {
            const isNotFound = item.status === "NOT_FOUND" || item.value === null;
            const isLowConfidence =
              !isNotFound && item.confidence !== null && item.confidence < LOW_CONFIDENCE_THRESHOLD;
            const isExpanded = expanded === item.field_id;

            return (
              <Fragment key={item.field_id}>
                <tr className="align-top">
                  <td className="px-4 py-3 font-medium text-slate-900">{item.display_name}</td>
                  <td className="px-4 py-3">
                    {isNotFound ? (
                      <span className="text-slate-400">Not Found</span>
                    ) : (
                      <div>
                        <span className="text-slate-800">{formatValue(item.value)}</span>
                        {isLowConfidence && (
                          <p className="mt-1 text-xs text-amber-600">
                            ⚠ Low Confidence: {Math.round((item.confidence ?? 0) * 100)}%
                          </p>
                        )}
                      </div>
                    )}
                  </td>
                  <td className="px-4 py-3 text-slate-600">
                    {item.confidence !== null ? `${Math.round(item.confidence * 100)}%` : "—"}
                  </td>
                  <td className="px-4 py-3 text-slate-600">{item.page ?? "—"}</td>
                  <td className="px-4 py-3 text-right">
                    {item.evidence && (
                      <button
                        type="button"
                        onClick={() => setExpanded(isExpanded ? null : item.field_id)}
                        className="text-xs font-medium text-slate-500 hover:text-slate-900"
                      >
                        {isExpanded ? "Hide evidence" : "Show evidence"}
                      </button>
                    )}
                  </td>
                </tr>
                {isExpanded && item.evidence && (
                  <tr>
                    <td colSpan={5} className="bg-slate-50 px-4 py-3">
                      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Evidence</p>
                      <p className="mt-1 text-sm italic text-slate-700">"{item.evidence}"</p>
                    </td>
                  </tr>
                )}
              </Fragment>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
