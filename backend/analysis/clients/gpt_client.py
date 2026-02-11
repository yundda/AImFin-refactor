# analysis/clients/gpt_client.py
import json
import requests
from django.conf import settings

class AIHTTPError(RuntimeError):
    pass

def complete_json(prompt: str, *, schema: dict, model: str | None = None, timeout: int | None = None) -> dict:
    """
    GMS 프록시 경유 Responses API 호출.
    - URL: {GMS_BASE_URL}/api.openai.com/v1/responses
    - Auth: Bearer {GMS_KEY}
    - Structured output: text.format.json_schema (Responses API 신규 규격)
    """
    url = f"{settings.GMS_BASE_URL.rstrip('/')}/api.openai.com/v1/responses"
    model = model or getattr(settings, "OPENAI_MODEL", "gpt-4o-realtime-preview-2024-10-01")
    timeout = timeout or int(getattr(settings, "OPENAI_TIMEOUT", 30))

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.GMS_KEY}",
    }

    payload = {
        "model": model,
        # 문자열 입력도 가능하지만, 호환성을 위해 message 형식으로 전달
        "input": [
            {"role": "user", "content": prompt}
        ],
        "text": {
            "format": {
                "type": "json_schema",
                # ★ json_schema라는 중첩 키가 아니라, format 안에 name/schema/strict를 직접 둡니다.
                "name": "RecommendResponse",
                "schema": schema,
                "strict": True,
            }
        },
        # 필요 시 생성 길이 제어
        "max_output_tokens": 2048,
        "temperature": 0.2,
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
    try:
        resp.raise_for_status()
    except requests.HTTPError as e:
        # GMS가 래핑한 에러 바디를 그대로 보여주도록
        raise AIHTTPError(
            f"AI {resp.status_code} error @ POST {url}\n{resp.text}"
        ) from e

    data = resp.json()

    # Responses API: output_text가 있으면 거기서 바로 텍스트 수거
    text = data.get("output_text")
    if not text:
        # fallback: output 배열에서 text 모으기
        parts = []
        for item in data.get("output", []):
            for c in item.get("content", []):
                if c.get("type") == "output_text":
                    parts.append(c.get("text", ""))
        text = "".join(parts)

    return json.loads(text)