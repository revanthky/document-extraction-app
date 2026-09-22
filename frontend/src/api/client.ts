import {
  ApiError,
  type DocumentResponse,
  type ExtractionResponse,
  type ExtractionResultResponse,
  type FetchModelsResponse,
  type ModelSettingsResponse,
  type ModelSettingsUpdateRequest,
  type TestConnectionResponse,
} from "../types";

// Vite's BASE_URL always has a trailing slash ("/" locally, "/workspace/<id>/<app>/" when
// served as a DKubeX app tile); strip it so callers can keep writing "/api/..." paths.
const BASE = import.meta.env.BASE_URL.replace(/\/$/, "");

function apiPath(path: string): string {
  return `${BASE}${path}`;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(apiPath(path), init);
  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;
    let detail: string | undefined;
    try {
      const body = await response.json();
      message = body.message ?? message;
      detail = body.detail;
    } catch {
      // response had no JSON body
    }
    throw new ApiError(message, response.status, detail);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

export const api = {
  health: () => request<{ status: string }>("/api/health"),

  getModelSettings: () => request<ModelSettingsResponse>("/api/settings/model"),

  updateModelSettings: (payload: ModelSettingsUpdateRequest) =>
    request<ModelSettingsResponse>("/api/settings/model", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),

  testConnection: () =>
    request<TestConnectionResponse>("/api/settings/model/test", { method: "POST" }),

  fetchModels: (apiBaseUrl: string, apiKey: string) =>
    request<FetchModelsResponse>("/api/settings/model/models", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ api_base_url: apiBaseUrl, api_key: apiKey }),
    }),

  uploadDocument: (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return request<DocumentResponse>("/api/documents/upload", {
      method: "POST",
      body: formData,
    });
  },

  getDocument: (documentId: string) => request<DocumentResponse>(`/api/documents/${documentId}`),

  documentPageUrl: (documentId: string, pageNum: number) =>
    apiPath(`/api/documents/${documentId}/pages/${pageNum}`),

  documentDownloadUrl: (documentId: string) => apiPath(`/api/documents/${documentId}/download`),

  deleteDocument: (documentId: string) =>
    request<{ status: string }>(`/api/documents/${documentId}`, { method: "DELETE" }),

  createExtraction: (payload: {
    document_id: string;
    fields: { name: string; display_name: string; description: string; data_type: string; required: boolean }[];
    instructions: string;
  }) =>
    request<ExtractionResponse>("/api/extractions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),

  getExtraction: (extractionId: string) => request<ExtractionResponse>(`/api/extractions/${extractionId}`),

  getExtractionResult: (extractionId: string) =>
    request<ExtractionResultResponse>(`/api/extractions/${extractionId}/result`),

  extractionDownloadJsonUrl: (extractionId: string) =>
    apiPath(`/api/extractions/${extractionId}/download/json`),

  extractionDownloadCsvUrl: (extractionId: string) =>
    apiPath(`/api/extractions/${extractionId}/download/csv`),
};

export { ApiError };
