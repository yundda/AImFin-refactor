# users/utils/oauth_kakao.py
import requests
from urllib.parse import urlencode
from django.conf import settings

KAKAO_AUTH = "https://kauth.kakao.com/oauth/authorize"
KAKAO_TOKEN = "https://kauth.kakao.com/oauth/token"
KAKAO_USERINFO = "https://kapi.kakao.com/v2/user/me"

def build_auth_url(state: str) -> str:
    # 카카오는 (웹/서버) PKCE 없어도 OK. BFF에서 서버 교환이면 state만 써도 충분.
    params = {
        "client_id": settings.KAKAO_CLIENT_ID,
        "redirect_uri": settings.KAKAO_REDIRECT_URI,
        "response_type": "code",
        "state": state,
        # scope가 필요하면 "profile_nickname,account_email" 등 추가 (동의 항목 세팅과 일치해야 함)
    }
    return f"{KAKAO_AUTH}?{urlencode(params)}"

def exchange_code_for_token(code: str):
    data = {
        "grant_type": "authorization_code",
        "client_id": settings.KAKAO_CLIENT_ID,
        "redirect_uri": settings.KAKAO_REDIRECT_URI,
        "code": code,
    }
    if settings.KAKAO_CLIENT_SECRET:
        data["client_secret"] = settings.KAKAO_CLIENT_SECRET

    headers = {"content-type": "application/x-www-form-urlencoded"}
    r = requests.post(KAKAO_TOKEN, data=data, headers=headers, timeout=10)
    r.raise_for_status()
    return r.json()  # {access_token, refresh_token?, ...}

def fetch_userinfo(access_token: str) -> dict:
    headers = {"Authorization": f"Bearer {access_token}"}
    r = requests.get(KAKAO_USERINFO, headers=headers, timeout=10)
    r.raise_for_status()
    return r.json()
