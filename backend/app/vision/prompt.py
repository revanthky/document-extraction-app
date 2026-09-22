from __future__ import annotations

import json
import re
from dataclasses import dataclass

from pydantic import BaseModel, Field, ValidationError

from app.core.exceptions import ModelResponseError

DEFAULT_INSTRUCTIONS = (
    "Extract only information that is present in the document.\n\n"
    "Do not guess or hallucinate values.\n\n"
    "If a requested field cannot be found, return null.\n\n"
    "Preserve the value as it appears in the document unless\n"
    "normalization is explicitly requested."
)


@dataclass
class FieldSpec:
    name: str
    description: str
    data_type: str
    required: bool


class ExtractedFieldSchema(BaseModel):
    name: str
    value: str | float | int | bool | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    page: int | None = None
    evidence: str | None = None


class ExtractionResponseSchema(BaseModel):
    fields: list[ExtractedFieldSchema]


def build_prompt(fields: list[FieldSpec], instructions: str) -> str:
    field_lines = []
    for f in fields:
        required = "required" if f.required else "optional"
        field_lines.append(
            f'- name: "{f.name}", type: {f.data_type}, {required}\n'
            f"  description: {f.description or '(no description provided)'}"
        )

    fields_block = "\n".join(field_lines)

    return f"""You are a precise document data extraction system. You are given one or
more page images from a single PDF document, rendered in order.

Extract exactly the following fields, and only these fields:

{fields_block}

Additional instructions from the user:
{instructions.strip() or DEFAULT_INSTRUCTIONS}

Respond with a single JSON object matching exactly this shape, with no markdown
fencing and no extra commentary:

{{
  "fields": [
    {{
      "name": "<field name, exactly as given above>",
      "value": <extracted value, or null if not found>,
      "confidence": <number between 0 and 1>,
      "page": <1-indexed page number the value was found on, or null>,
      "evidence": "<short verbatim quote from the document supporting this value, or null>"
    }}
  ]
}}

Return one entry in "fields" for every requested field, in the same order. If a
field cannot be found in the document, set "value" to null, "page" to null,
"evidence" to null, and use a low confidence score."""


_MARKDOWN_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


def _strip_markdown_fence(text: str) -> str:
    return _MARKDOWN_FENCE_RE.sub("", text).strip()


def parse_and_validate_response(raw_text: str) -> ExtractionResponseSchema:
    """Parse the model's raw text into a validated ExtractionResponseSchema.

    Tries the raw text first, then a markdown-fence-stripped version. Never
    silently accepts malformed data -- raises ModelResponseError with a
    truncated snippet of the raw response for diagnosis.
    """
    candidates = [raw_text, _strip_markdown_fence(raw_text)]
    last_error: Exception | None = None

    for candidate in candidates:
        try:
            data = json.loads(candidate)
            return ExtractionResponseSchema.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as exc:
            last_error = exc
            continue

    snippet = raw_text[:500]
    raise ModelResponseError(
        "The Vision Model did not return valid structured data.",
        detail=f"Parse error: {last_error}. Raw response (truncated): {snippet!r}",
    )
