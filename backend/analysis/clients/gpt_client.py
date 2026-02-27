# analysis/clients/gpt_client.py
import json
import requests
import time
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

class AIHTTPError(RuntimeError):
    pass

def complete_json(prompt: str, *, schema: dict, model: str | None = None, timeout: int | None = None, call_name: str = "default") -> dict:
    """
    설정에 따라 OpenAI(GMS) 또는 Google Gemini를 호출하여 JSON 결과를 반환.
    """
    start_time = time.perf_counter()

    # --- 1. 프로바이더 분기 ---
    provider = getattr(settings, "AI_PROVIDER", "openai").lower()
    
    if provider == "gemini":
        result = _call_gemini(prompt, schema=schema, model=model, timeout=timeout, call_name=call_name, start_time=start_time)
    else:
        result = _call_openai_gms(prompt, schema=schema, model=model, timeout=timeout, call_name=call_name, start_time=start_time)

    return result

def _call_openai_gms(prompt: str, *, schema: dict, model: str, timeout: int, call_name: str, start_time: float) -> dict:
    url = f"{settings.GMS_BASE_URL.rstrip('/')}/api.openai.com/v1/responses"
    model = model or getattr(settings, "OPENAI_MODEL", "gpt-4o-mini")
    timeout = timeout or int(getattr(settings, "OPENAI_TIMEOUT", 30))

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.GMS_KEY}",
    }
    payload = {
        "model": model,
        "input": [{"role": "user", "content": prompt}],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "RecommendResponse",
                "schema": schema,
                "strict": True,
            }
        },
        "max_output_tokens": 2048,
        "temperature": 0.2,
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
    latency_ms = (time.perf_counter() - start_time) * 1000

    try:
        resp.raise_for_status()
    except requests.HTTPError as e:
        raise AIHTTPError(f"OpenAI GMS {resp.status_code} error: {resp.text}") from e

    data = resp.json()
    total_tokens = data.get("usage", {}).get("total_tokens", 0)
    
    # [AI_METRICS] 포맷 유지 (Actual Data 로깅)
    mode = "legacy" if "v1" in call_name else "hardened"
    call_type = "single_pass" if "single" in call_name else ("proposal" if "data" in call_name else "comment")
    print(f"\n[AI_METRICS] mode:{mode} call:{call_type} provider:openai latency:{latency_ms:.2f}ms tokens_total:{total_tokens}")

    text = data.get("output_text") or ""
    if not text:
        parts = []
        for item in data.get("output", []):
            for c in item.get("content", []):
                if c.get("type") == "output_text":
                    parts.append(c.get("text", ""))
        text = "".join(parts)

    result = json.loads(text)
    result["_metrics"] = {"latency_ms": latency_ms, "total_tokens": total_tokens}
    return result

def _sanitize_schema_for_gemini(schema: dict) -> dict:
    if not isinstance(schema, dict):
        return schema
    unsupported = ["additionalProperties", "minItems", "maxItems", "pattern", "format"]
    new_schema = {k: v for k, v in schema.items() if k not in unsupported}
    if "properties" in new_schema:
        new_schema["properties"] = {
            k: _sanitize_schema_for_gemini(v) for k, v in new_schema["properties"].items()
        }
    if "items" in new_schema:
        new_schema["items"] = _sanitize_schema_for_gemini(new_schema["items"])
    return new_schema 

def _call_gemini(prompt: str, *, schema: dict, model: str, timeout: int, call_name: str, start_time: float) -> dict:
    model = model or getattr(settings, "GEMINI_MODEL", "gemini-2.0-flash")
    api_key = getattr(settings, "GEMINI_API_KEY", "")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    timeout = timeout or int(getattr(settings, "AI_TIMEOUT", 30))

    headers = {"Content-Type": "application/json"}
    sanitized_schema = _sanitize_schema_for_gemini(schema)
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt + "\n\nCRITICAL: Follow field names exactly."}]
        }],
        "generationConfig": {
            "response_mime_type": "application/json",
            "response_schema": sanitized_schema,
            "temperature": 0.1,
            "maxOutputTokens": 4096,
        }
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
    latency_ms = (time.perf_counter() - start_time) * 1000

    try:
        resp.raise_for_status()
    except requests.HTTPError as e:
        raise AIHTTPError(f"Gemini {resp.status_code} error: {resp.text}") from e

    data = resp.json()
    total_tokens = data.get("usageMetadata", {}).get("totalTokenCount", 0)
    
    # [AI_METRICS] 포맷 유지 (Actual Data 로깅)
    mode = "legacy" if "v1" in call_name else "hardened"
    call_type = "single_pass" if "single" in call_name else ("proposal" if "data" in call_name else "comment")
    print(f"\n[AI_METRICS] mode:{mode} call:{call_type} provider:gemini latency:{latency_ms:.2f}ms tokens_total:{total_tokens}")

    try:
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        result = json.loads(text)
    except Exception as e:
        raise AIHTTPError(f"Gemini parsing error: {str(e)}")

    result["_metrics"] = {"latency_ms": latency_ms, "total_tokens": total_tokens}
    return result
