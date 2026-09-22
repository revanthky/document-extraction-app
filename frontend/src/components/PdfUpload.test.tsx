import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ApiError, api } from "../api/client";
import { PdfUpload } from "./PdfUpload";

vi.mock("../api/client", async () => {
  const actual = await vi.importActual<typeof import("../api/client")>("../api/client");
  return {
    ...actual,
    api: { ...actual.api, uploadDocument: vi.fn() },
  };
});

function makeFile(name: string, type: string) {
  return new File(["dummy content"], name, { type });
}

function getFileInput(): HTMLInputElement {
  return window.document.querySelector('input[type="file"]') as HTMLInputElement;
}

describe("PdfUpload", () => {
  it("rejects non-PDF files with the exact error message", async () => {
    render(<PdfUpload document={null} onUploaded={vi.fn()} onRemove={vi.fn()} />);
    fireEvent.change(getFileInput(), { target: { files: [makeFile("notes.txt", "text/plain")] } });

    expect(await screen.findByText("Only PDF documents are supported.")).toBeInTheDocument();
    expect(api.uploadDocument).not.toHaveBeenCalled();
  });

  it("uploads a valid PDF and calls onUploaded", async () => {
    const onUploaded = vi.fn();
    const uploaded = {
      id: "doc-1",
      original_filename: "policy.pdf",
      mime_type: "application/pdf",
      file_size: 1024,
      page_count: 2,
      document_type: null,
      status: "UPLOADED",
      created_at: "",
      updated_at: "",
    };
    vi.mocked(api.uploadDocument).mockResolvedValue(uploaded);

    render(<PdfUpload document={null} onUploaded={onUploaded} onRemove={vi.fn()} />);
    fireEvent.change(getFileInput(), { target: { files: [makeFile("policy.pdf", "application/pdf")] } });

    await waitFor(() => expect(onUploaded).toHaveBeenCalledWith(uploaded));
  });

  it("shows an error message when the upload API call fails", async () => {
    vi.mocked(api.uploadDocument).mockRejectedValue(
      new ApiError("File exceeds the maximum allowed size", 413)
    );

    render(<PdfUpload document={null} onUploaded={vi.fn()} onRemove={vi.fn()} />);
    fireEvent.change(getFileInput(), { target: { files: [makeFile("big.pdf", "application/pdf")] } });

    expect(await screen.findByText(/File exceeds the maximum allowed size/)).toBeInTheDocument();
  });

  it("renders uploaded document metadata and a Remove button", () => {
    const onRemove = vi.fn();
    render(
      <PdfUpload
        document={{
          id: "doc-1",
          original_filename: "policy.pdf",
          mime_type: "application/pdf",
          file_size: 2048,
          page_count: 3,
          document_type: null,
          status: "UPLOADED",
          created_at: "",
          updated_at: "",
        }}
        onUploaded={vi.fn()}
        onRemove={onRemove}
      />
    );

    expect(screen.getByText("policy.pdf")).toBeInTheDocument();
    fireEvent.click(screen.getByText("Remove"));
    expect(onRemove).toHaveBeenCalled();
  });
});
