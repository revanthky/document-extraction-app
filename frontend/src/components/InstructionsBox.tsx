export const DEFAULT_INSTRUCTIONS = `Extract only information that is present in the document.

Do not guess or hallucinate values.

If a requested field cannot be found, return null.

Preserve the value as it appears in the document unless
normalization is explicitly requested.`;

interface InstructionsBoxProps {
  value: string;
  onChange: (value: string) => void;
}

export function InstructionsBox({ value, onChange }: InstructionsBoxProps) {
  return (
    <div>
      <label className="mb-1 block text-sm font-medium text-slate-700">Additional Instructions</label>
      <textarea
        className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
        rows={5}
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    </div>
  );
}
