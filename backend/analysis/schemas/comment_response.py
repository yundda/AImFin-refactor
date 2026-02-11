# analysis/schemas/comment_response.py
COMMENT_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "rationale": {"type": "string"},
        "summary": {"type": "string"}
    },
    "required": ["rationale", "summary"],
    "additionalProperties": False
}