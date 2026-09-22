import { useRef, useState } from "react";
import type { DragEvent } from "react";
import { ApiError, api } from "../api/client";
import type { DocumentResponse } from "../types";

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

interface PdfUploadProps {
  document: DocumentResponse | null;
  onUploaded: (document: DocumentResponse) => void;
  onRemove: () => void;
}

export function PdfUpload({ document, onUploaded, onRemove }: PdfUploadProps) {
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  async function handleFile(file: File) {
    setError(null);
    if (file.type !== "application/pdf") {
      setError("Only PDF documents are supported.");
      return;
    }
    setUploading(true);
    try {
      const uploaded = await api.uploadDocument(file);
      onUploaded(uploaded);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to upload document.");
    } finally {
      setUploading(false);
    }
  }

  function handleDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setDragActive(false);
    const file = e.dataTransfer.files?.[0];
    if (file) handleFile(file);
  }

  if (document) {
    return (
      <div className="rounded-lg border border-slate-200 bg-white p-4">
        <div className="flex items-start justify-between">
          <div>
            <p className="font-medium text-slate-900">{document.original_filename}</p>
            <p className="text-sm text-slate-500">
              {formatFileSize(document.file_size)} · {document.page_count ?? "?"} page
              {document.page_count === 1 ? "" : "s"} · {document.status}
            </p>
          </div>
          <button
            type="button"
            onClick={onRemove}
            className="rounded-md border border-slate-300 px-3 py-1 text-sm text-slate-600 hover:bg-slate-50"
          >
            Remove
          </button>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div
        role="button"
        tabIndex={0}
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setDragActive(true);
        }}
        onDragLeave={() => setDragActive(false)}
        onDrop={handleDrop}
        className={`flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-10 text-center transition-colors ${
          dragActive ? "border-slate-500 bg-slate-50" : "border-slate-300"
        }`}
      >
        <p className="font-medium text-slate-700">Upload PDF Document</p>
        <p className="mt-1 text-sm text-slate-500">Drag & drop a PDF here, or</p>
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            inputRef.current?.click();
          }}
          disabled={uploading}
          className="mt-3 rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
        >
          {uploading ? "Uploading..." : "Browse PDF"}
        </button>
        <p className="mt-3 text-xs text-slate-400">Only PDF files are supported.</p>
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) handleFile(file);
            e.target.value = "";
          }}
        />
      </div>
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
    </div>
  );
}
