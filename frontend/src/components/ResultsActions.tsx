import { useState } from "react";
import { api } from "../api/client";
import type { ExtractionResultResponse } from "../types";

interface ResultsActionsProps {
  extractionId: string;
  result: ExtractionResultResponse;
  onExtractAgain: () => void;
  onClear: () => void;
}

export function ResultsActions({ extractionId, result, onExtractAgain, onClear }: ResultsActionsProps) {
  const [copied, setCopied] = useState(false);

  async function handleCopyJson() {
    await navigator.clipboard.writeText(JSON.stringify(result, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  return (
    <div className="flex flex-wrap gap-2">
      <button
        type="button"
        onClick={handleCopyJson}
        className="rounded-md border border-slate-300 px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50"
      >
        {copied ? "Copied!" : "Copy JSON"}
      </button>
      <a
        href={api.extractionDownloadJsonUrl(extractionId)}
        className="rounded-md border border-slate-300 px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50"
      >
        Download JSON
      </a>
      <a
        href={api.extractionDownloadCsvUrl(extractionId)}
        className="rounded-md border border-slate-300 px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50"
      >
        Download CSV
      </a>
      <button
        type="button"
        onClick={onExtractAgain}
        className="rounded-md bg-slate-900 px-3 py-1.5 text-sm font-medium text-white hover:bg-slate-800"
      >
        Extract Again
      </button>
      <button
        type="button"
        onClick={onClear}
        className="rounded-md border border-slate-300 px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50"
      >
        Clear
      </button>
    </div>
  );
}
