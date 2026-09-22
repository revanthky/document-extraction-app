import { useEffect, useRef, useState } from "react";
import { ApiError, api } from "../api/client";
import { ExtractionProgress, EXTRACTION_STAGES } from "../components/ExtractionProgress";
import { FieldEditor } from "../components/FieldEditor";
import { DEFAULT_INSTRUCTIONS, InstructionsBox } from "../components/InstructionsBox";
import { PdfPreview } from "../components/PdfPreview";
import { PdfUpload } from "../components/PdfUpload";
import { ResultsActions } from "../components/ResultsActions";
import { ResultsTable } from "../components/ResultsTable";
import { useModelSettings } from "../hooks/useModelSettings";
import type { DocumentResponse, ExtractionResultResponse, FieldDefinition } from "../types";

export function ExtractionPage() {
  const { isConfigured, loading: settingsLoading } = useModelSettings();
  const [document, setDocument] = useState<DocumentResponse | null>(null);
  const [fields, setFields] = useState<FieldDefinition[]>([]);
  const [instructions, setInstructions] = useState(DEFAULT_INSTRUCTIONS);
  const [extracting, setExtracting] = useState(false);
  const [stage, setStage] = useState(0);
  const [result, setResult] = useState<ExtractionResultResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const stageTimer = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    return () => {
      if (stageTimer.current) clearInterval(stageTimer.current);
    };
  }, []);

  const namedFields = fields.filter((f) => f.name.trim().length > 0);
  const canExtract = Boolean(document) && namedFields.length > 0 && isConfigured && !extracting;

  const validationMessages: string[] = [];
  if (!document) validationMessages.push("Upload a PDF document.");
  if (namedFields.length === 0) validationMessages.push("Define at least one field to extract.");
  if (!settingsLoading && !isConfigured) validationMessages.push("Configure the Vision Model in Settings.");

  function resetForNewDocument() {
    setResult(null);
    setError(null);
  }

  async function runExtraction() {
    if (!document) return;
    setExtracting(true);
    setError(null);
    setResult(null);
    setStage(0);

    stageTimer.current = setInterval(() => {
      setStage((s) => Math.min(s + 1, EXTRACTION_STAGES.length - 1));
    }, 900);

    try {
      const extraction = await api.createExtraction({
        document_id: document.id,
        fields: namedFields.map((f) => ({
          name: f.name.trim(),
          display_name: f.name.trim(),
          description: f.description,
          data_type: f.dataType,
          required: f.required,
        })),
        instructions,
      });
      const fullResult = await api.getExtractionResult(extraction.id);
      setStage(EXTRACTION_STAGES.length - 1);
      setResult(fullResult);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Extraction failed unexpectedly.");
    } finally {
      if (stageTimer.current) clearInterval(stageTimer.current);
      setExtracting(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="space-y-4">
          <PdfUpload
            document={document}
            onUploaded={(doc) => {
              setDocument(doc);
              resetForNewDocument();
            }}
            onRemove={() => {
              setDocument(null);
              resetForNewDocument();
            }}
          />
          {document && document.page_count && (
            <PdfPreview documentId={document.id} pageCount={document.page_count} />
          )}
        </div>

        <div className="space-y-4">
          <FieldEditor fields={fields} onChange={setFields} />
          <InstructionsBox value={instructions} onChange={setInstructions} />

          <div>
            <button
              type="button"
              onClick={runExtraction}
              disabled={!canExtract}
              className="w-full rounded-md bg-slate-900 px-4 py-2.5 text-sm font-medium text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-40"
            >
              Extract Document
            </button>
            {!canExtract && !extracting && validationMessages.length > 0 && (
              <ul className="mt-2 space-y-0.5 text-xs text-slate-500">
                {validationMessages.map((m) => (
                  <li key={m}>• {m}</li>
                ))}
              </ul>
            )}
          </div>

          {extracting && <ExtractionProgress currentStage={stage} />}

          {error && (
            <div className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-800">
              <p className="font-medium">Extraction Failed</p>
              <p className="mt-1">{error}</p>
              <button
                type="button"
                onClick={runExtraction}
                className="mt-3 rounded-md border border-red-300 px-3 py-1 text-sm font-medium hover:bg-red-100"
              >
                Retry
              </button>
            </div>
          )}
        </div>
      </div>

      {result && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-900">Extraction Results</h2>
            <ResultsActions
              extractionId={result.extraction.id}
              result={result}
              onExtractAgain={runExtraction}
              onClear={() => setResult(null)}
            />
          </div>
          <ResultsTable results={result.results} />
        </div>
      )}
    </div>
  );
}
