import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { ExtractionResultItem } from "../types";
import { ResultsTable } from "./ResultsTable";

function item(overrides: Partial<ExtractionResultItem> = {}): ExtractionResultItem {
  return {
    field_id: "f1",
    name: "policy_number",
    display_name: "Policy Number",
    data_type: "String",
    required: true,
    value: "POL-123456",
    normalized_value: null,
    confidence: 0.96,
    status: "FOUND",
    page: 1,
    document_section: null,
    evidence: "Policy Number: POL-123456",
    bounding_box: null,
    validation_status: "OK",
    is_verified: false,
    is_user_edited: false,
    ...overrides,
  };
}

describe("ResultsTable", () => {
  it("renders the field name, value, confidence, and page", () => {
    render(<ResultsTable results={[item()]} />);
    expect(screen.getByText("Policy Number")).toBeInTheDocument();
    expect(screen.getByText("POL-123456")).toBeInTheDocument();
    expect(screen.getByText("96%")).toBeInTheDocument();
    expect(screen.getByText("1")).toBeInTheDocument();
  });

  it("shows 'Not Found' for fields with a null value", () => {
    render(<ResultsTable results={[item({ value: null, status: "NOT_FOUND", confidence: null, page: null })]} />);
    expect(screen.getByText("Not Found")).toBeInTheDocument();
  });

  it("shows a low confidence warning below the threshold", () => {
    render(<ResultsTable results={[item({ confidence: 0.61 })]} />);
    expect(screen.getByText(/Low Confidence: 61%/)).toBeInTheDocument();
  });

  it("does not show a low confidence warning at or above the threshold", () => {
    render(<ResultsTable results={[item({ confidence: 0.7 })]} />);
    expect(screen.queryByText(/Low Confidence/)).not.toBeInTheDocument();
  });

  it("reveals evidence text when 'Show evidence' is clicked", () => {
    render(<ResultsTable results={[item()]} />);
    expect(screen.queryByText(/Policy Number: POL-123456/)).not.toBeInTheDocument();
    fireEvent.click(screen.getByText("Show evidence"));
    expect(screen.getByText(/Policy Number: POL-123456/)).toBeInTheDocument();
  });
});
