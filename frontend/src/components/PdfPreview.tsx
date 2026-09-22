import { useState } from "react";
import { api } from "../api/client";

interface PdfPreviewProps {
  documentId: string;
  pageCount: number;
}

export function PdfPreview({ documentId, pageCount }: PdfPreviewProps) {
  const [page, setPage] = useState(1);
  const [zoom, setZoom] = useState(1);

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <p className="mb-3 text-sm font-medium text-slate-700">PDF Preview</p>
      <div className="flex justify-center overflow-auto rounded-md bg-slate-100 p-4" style={{ minHeight: 320 }}>
        <img
          key={page}
          src={api.documentPageUrl(documentId, page)}
          alt={`Page ${page}`}
          style={{ transform: `scale(${zoom})`, transformOrigin: "top center" }}
          className="max-w-full shadow-sm"
        />
      </div>
      <div className="mt-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setZoom((z) => Math.max(0.5, z - 0.25))}
            className="rounded-md border border-slate-300 px-2 py-1 text-xs text-slate-600 hover:bg-slate-50"
          >
            −
          </button>
          <span className="text-xs text-slate-500">{Math.round(zoom * 100)}%</span>
          <button
            type="button"
            onClick={() => setZoom((z) => Math.min(2, z + 0.25))}
            className="rounded-md border border-slate-300 px-2 py-1 text-xs text-slate-600 hover:bg-slate-50"
          >
            +
          </button>
        </div>
        <p className="text-sm text-slate-500">
          Page {page} of {pageCount}
        </p>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page <= 1}
            className="rounded-md border border-slate-300 px-3 py-1 text-sm text-slate-700 hover:bg-slate-50 disabled:opacity-40"
          >
            Previous
          </button>
          <button
            type="button"
            onClick={() => setPage((p) => Math.min(pageCount, p + 1))}
            disabled={page >= pageCount}
            className="rounded-md border border-slate-300 px-3 py-1 text-sm text-slate-700 hover:bg-slate-50 disabled:opacity-40"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
