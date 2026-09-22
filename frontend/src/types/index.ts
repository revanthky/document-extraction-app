export const DATA_TYPES = [
  "String",
  "Integer",
  "Decimal",
  "Date",
  "Boolean",
  "Email",
  "Phone",
  "Currency",
] as const;

export type DataType = (typeof DATA_TYPES)[number];

export interface FieldDefinition {
  id: string;
  name: string;
  description: string;
  dataType: DataType;
  required: boolean;
}

export interface DocumentResponse {
  id: string;
  original_filename: string;
  mime_type: string;
  file_size: number;
  page_count: number | null;
  document_type: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface ModelSettingsResponse {
  provider: string;
  api_base_url: string;
  api_key_masked: string;
  api_key_configured: boolean;
  model_name: string;
  temperature: number;
  max_tokens: number;
  timeout: number;
  pdf_render_dpi: number;
}

export interface ModelSettingsUpdateRequest {
  provider: string;
  api_base_url: string;
  api_key?: string | null;
  model_name: string;
  temperature: number;
  max_tokens: number;
  timeout: number;
  pdf_render_dpi: number;
}

export interface TestConnectionResponse {
  success: boolean;
  message: string;
  model: string | null;
  response_time_ms: number | null;
}

export interface FetchModelsResponse {
  models: string[];
}

export interface ExtractionResponse {
  id: string;
  document_id: string;
  status: "PENDING" | "PROCESSING" | "COMPLETED" | "FAILED";
  model_provider: string;
  model_name: string;
  instructions: string | null;
  processing_time_ms: number | null;
  fields_requested: number;
  fields_extracted: number;
  fields_not_found: number;
  validation_failures: number;
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
}

export interface ExtractionResultItem {
  field_id: string;
  name: string;
  display_name: string;
  data_type: string;
  required: boolean;
  value: string | number | boolean | null;
  normalized_value: string | number | boolean | null;
  confidence: number | null;
  status: "FOUND" | "NOT_FOUND" | "ERROR";
  page: number | null;
  document_section: string | null;
  evidence: string | null;
  bounding_box: Record<string, unknown> | null;
  validation_status: string | null;
  is_verified: boolean;
  is_user_edited: boolean;
}

export interface ExtractionResultResponse {
  extraction: ExtractionResponse;
  results: ExtractionResultItem[];
}

export class ApiError extends Error {
  status: number;
  detail?: string;

  constructor(message: string, status: number, detail?: string) {
    super(message);
    this.status = status;
    this.detail = detail;
  }
}
