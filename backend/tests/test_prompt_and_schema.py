from __future__ import annotations

import pytest

from app.core.exceptions import ModelResponseError
from app.vision.prompt import FieldSpec, build_prompt, parse_and_validate_response


def _fields() -> list[FieldSpec]:
    return [
        FieldSpec(name="policy_number", description="Extract the policy number", data_type="String", required=True),
        FieldSpec(name="patient_name", description="Full name of the patient", data_type="String", required=True),
    ]


def test_build_prompt_includes_all_field_names_and_instructions():
    prompt = build_prompt(_fields(), "Do not guess.")
    assert "policy_number" in prompt
    assert "patient_name" in prompt
    assert "Do not guess." in prompt
    assert "JSON" in prompt


def test_build_prompt_falls_back_to_default_instructions_when_blank():
    prompt = build_prompt(_fields(), "")
    assert "Do not guess or hallucinate" in prompt


def test_parse_valid_json_response():
    raw = '{"fields": [{"name": "policy_number", "value": "POL-1", "confidence": 0.9, "page": 1, "evidence": "POL-1"}]}'
    result = parse_and_validate_response(raw)
    assert result.fields[0].name == "policy_number"
    assert result.fields[0].value == "POL-1"


def test_parse_strips_markdown_fencing():
    raw = '```json\n{"fields": [{"name": "x", "value": null, "confidence": 0.1, "page": null, "evidence": null}]}\n```'
    result = parse_and_validate_response(raw)
    assert result.fields[0].name == "x"
    assert result.fields[0].value is None


def test_parse_invalid_json_raises_model_response_error():
    with pytest.raises(ModelResponseError) as excinfo:
        parse_and_validate_response("not json at all")
    assert "truncated" in str(excinfo.value.detail).lower() or "Raw response" in str(excinfo.value.detail)


def test_parse_missing_required_key_raises():
    with pytest.raises(ModelResponseError):
        parse_and_validate_response('{"not_fields": []}')


def test_parse_out_of_range_confidence_raises():
    raw = '{"fields": [{"name": "x", "value": "y", "confidence": 1.5, "page": 1, "evidence": "y"}]}'
    with pytest.raises(ModelResponseError):
        parse_and_validate_response(raw)
