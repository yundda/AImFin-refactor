# users/utils/pkce_store.py
from django.core.cache import cache

KEY_FMT = "google:pkce:{state}"
TTL = 600  # 10분

def save_verifier(state: str, code_verifier: str):
    cache.set(KEY_FMT.format(state=state), code_verifier, timeout=TTL)

def pop_verifier(state: str) -> str | None:
    key = KEY_FMT.format(state=state)
    val = cache.get(key)
    if val:
        cache.delete(key)
    return val

NONCE_KEY = "google:nonce:{state}"

def save_nonce(state: str, nonce: str):
    cache.set(NONCE_KEY.format(state=state), nonce, timeout=TTL)

def pop_nonce(state: str) -> str | None:
    key = NONCE_KEY.format(state=state)
    val = cache.get(key)
    if val:
        cache.delete(key)
    return val

# ★ 추가: purpose/next 등 부가 메타 저장 (선택)
META_KEY = "google:meta:{state}"

def save_meta(state: str, meta: dict):
    cache.set(META_KEY.format(state=state), meta or {}, timeout=TTL)

def pop_meta(state: str) -> dict:
    key = META_KEY.format(state=state)
    val = cache.get(key) or {}
    cache.delete(key)
    return val
