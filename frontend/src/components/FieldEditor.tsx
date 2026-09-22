import { DATA_TYPES, type DataType, type FieldDefinition } from "../types";

interface FieldEditorProps {
  fields: FieldDefinition[];
  onChange: (fields: FieldDefinition[]) => void;
}

function createEmptyField(): FieldDefinition {
  return {
    id: crypto.randomUUID(),
    name: "",
    description: "",
    dataType: "String",
    required: false,
  };
}

export function FieldEditor({ fields, onChange }: FieldEditorProps) {
  function updateField(id: string, patch: Partial<FieldDefinition>) {
    onChange(fields.map((f) => (f.id === id ? { ...f, ...patch } : f)));
  }

  function removeField(id: string) {
    onChange(fields.filter((f) => f.id !== id));
  }

  function addField() {
    onChange([...fields, createEmptyField()]);
  }

  return (
    <div>
      <p className="mb-3 text-sm font-medium text-slate-700">Fields to Extract</p>
      <div className="space-y-3">
        {fields.map((field) => (
          <div key={field.id} className="rounded-lg border border-slate-200 bg-white p-4">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="mb-1 block text-xs font-medium text-slate-500">Field Name</label>
                <input
                  className="w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm"
                  value={field.name}
                  onChange={(e) => updateField(field.id, { name: e.target.value })}
                  placeholder="Policy Number"
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-slate-500">Type</label>
                <select
                  className="w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm"
                  value={field.dataType}
                  onChange={(e) => updateField(field.id, { dataType: e.target.value as DataType })}
                >
                  {DATA_TYPES.map((type) => (
                    <option key={type} value={type}>
                      {type}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <div className="mt-3">
              <label className="mb-1 block text-xs font-medium text-slate-500">Description</label>
              <input
                className="w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm"
                value={field.description}
                onChange={(e) => updateField(field.id, { description: e.target.value })}
                placeholder="Extract the policy number"
              />
            </div>
            <div className="mt-3 flex items-center justify-between">
              <label className="flex items-center gap-2 text-sm text-slate-600">
                <input
                  type="checkbox"
                  checked={field.required}
                  onChange={(e) => updateField(field.id, { required: e.target.checked })}
                />
                Required
              </label>
              <button
                type="button"
                onClick={() => removeField(field.id)}
                className="text-sm text-red-600 hover:underline"
              >
                Remove
              </button>
            </div>
          </div>
        ))}
      </div>
      <button
        type="button"
        onClick={addField}
        className="mt-3 rounded-md border border-dashed border-slate-300 px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50"
      >
        + Add Field
      </button>
    </div>
  );
}
