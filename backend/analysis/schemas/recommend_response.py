# analysis/schemas/recommend_response.py
RECOMMEND_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "allocations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "bucket": {"type": "string"},
                    "weight_pct": {"type": "number"},
                    "assets": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "code": {"type": "string"},
                                "weight_pct": {"type": "number"}
                            },
                            "required": ["code", "weight_pct"],
                            "additionalProperties": False
                        }
                    }
                },
                "required": ["bucket", "weight_pct", "assets"],
                "additionalProperties": False
            },
            "minItems": 1
        },
        "rationale": {"type": "string"},
        "summary": {"type": "string"},
    },
    "required": ["allocations", "rationale", "summary"],
    "additionalProperties": False
}