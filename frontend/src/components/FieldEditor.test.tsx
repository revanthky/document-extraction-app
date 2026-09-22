import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { FieldDefinition } from "../types";
import { FieldEditor } from "./FieldEditor";

function field(overrides: Partial<FieldDefinition> = {}): FieldDefinition {
  return {
    id: "1",
    name: "",
    description: "",
    dataType: "String",
    required: false,
    ...overrides,
  };
}

describe("FieldEditor", () => {
  it("renders no fields by default (no hardcoded example fields)", () => {
    render(<FieldEditor fields={[]} onChange={vi.fn()} />);
    expect(screen.queryByDisplayValue(/Policy Number/i)).not.toBeInTheDocument();
  });

  it("adds a new empty field when '+ Add Field' is clicked", () => {
    const onChange = vi.fn();
    render(<FieldEditor fields={[]} onChange={onChange} />);
    fireEvent.click(screen.getByText("+ Add Field"));
    expect(onChange).toHaveBeenCalledTimes(1);
    const newFields = onChange.mock.calls[0][0] as FieldDefinition[];
    expect(newFields).toHaveLength(1);
    expect(newFields[0].name).toBe("");
  });

  it("removes a field when Remove is clicked", () => {
    const onChange = vi.fn();
    render(<FieldEditor fields={[field({ id: "a" }), field({ id: "b" })]} onChange={onChange} />);
    const removeButtons = screen.getAllByText("Remove");
    fireEvent.click(removeButtons[0]);
    const newFields = onChange.mock.calls[0][0] as FieldDefinition[];
    expect(newFields).toHaveLength(1);
    expect(newFields[0].id).toBe("b");
  });

  it("updates the field name on input", () => {
    const onChange = vi.fn();
    render(<FieldEditor fields={[field({ id: "a" })]} onChange={onChange} />);
    fireEvent.change(screen.getByPlaceholderText("Policy Number"), {
      target: { value: "Invoice Number" },
    });
    const newFields = onChange.mock.calls[0][0] as FieldDefinition[];
    expect(newFields[0].name).toBe("Invoice Number");
  });

  it("toggles the required checkbox", () => {
    const onChange = vi.fn();
    render(<FieldEditor fields={[field({ id: "a", required: false })]} onChange={onChange} />);
    fireEvent.click(screen.getByRole("checkbox"));
    const newFields = onChange.mock.calls[0][0] as FieldDefinition[];
    expect(newFields[0].required).toBe(true);
  });

  it("supports every documented data type", () => {
    render(<FieldEditor fields={[field({ id: "a" })]} onChange={vi.fn()} />);
    const select = screen.getByRole("combobox") as HTMLSelectElement;
    const options = Array.from(select.options).map((o) => o.value);
    expect(options).toEqual([
      "String",
      "Integer",
      "Decimal",
      "Date",
      "Boolean",
      "Email",
      "Phone",
      "Currency",
    ]);
  });
});
