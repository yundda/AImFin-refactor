# analysis/schemas/compare_response.py
from __future__ import annotations

COMPARE_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "rationale": {"type": "string"},
        # summary는 고객 코멘트. 문자열 또는 문자열 배열 허용.
        "summary": {"type": "string"},
        "risks": {"type": "string"},
    },
    "required": ["rationale", "summary", "risks"],
    "additionalProperties": False,
}