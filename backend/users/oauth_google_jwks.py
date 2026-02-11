from jose import jwt
import requests
from functools import lru_cache
from django.conf import settings
import time

GOOGLE_JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs"
GOOGLE_ISS = {"https://accounts.google.com", "accounts.google.com"}

@lru_cache(maxsize=1)
def _jwks():
    # 단순 캐시: 5분마다 새로 받고 싶으면 캐시 무효화 로직 추가
    return requests.get(GOOGLE_JWKS_URL, timeout=5).json()

def verify_id_token(id_token: str, *, nonce: str | None = None, access_token: str | None = None) -> dict:
    options = {
        "verify_aud": True,
        "verify_iss": True,
        "verify_exp": True,
        "verify_at_hash": bool(access_token),  # access_token 있으면 at_hash 검증
    }
    payload = jwt.decode(
        id_token,
        _jwks(),               # jose가 kid에 맞는 키를 자동 선택
        algorithms=["RS256"],
        audience=settings.GOOGLE_CLIENT_ID,
        issuer=list(GOOGLE_ISS),
        access_token=access_token,  # ★ 핵심
        options=options,
    )
    if nonce and payload.get("nonce") != nonce:
        raise ValueError("Invalid nonce")
    # leeway(시계 오차) 필요하면: jwt.get_unverified_header & 수동 검사로 여유 주기
    return payload
