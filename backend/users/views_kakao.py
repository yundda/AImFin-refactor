# users/views_kakao.py
from django.conf import settings
from django.shortcuts import redirect
from django.utils.crypto import get_random_string
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from urllib.parse import quote_plus

from .utils.pkce_store import save_nonce, pop_nonce
from .utils.oauth_kakao import build_auth_url, exchange_code_for_token, fetch_userinfo
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

def issue_tokens(user):
    r = RefreshToken.for_user(user)
    return {"access": str(r.access_token), "refresh": str(r)}

class KakaoStartView(APIView):
    def get(self, request):
        state = get_random_string(32)
        save_nonce(state, "1")
        url = build_auth_url(state)
        return redirect(url)

class KakaoCallbackView(APIView):
    def get(self, request):
        code = request.query_params.get("code")
        state = request.query_params.get("state")
        if not code or not state:
            return Response({"detail": "missing code/state"}, status=400)

        marker = pop_nonce(state)
        if not marker:
            return Response({"detail": "invalid state"}, status=400)

        # 1) 코드→토큰
        try:
            token_json = exchange_code_for_token(code)
        except Exception as e:
            return Response({"detail": f"token exchange failed: {e}"}, status=400)

        kakao_access_token = token_json.get("access_token")
        if not kakao_access_token:
            return Response({"detail": "no access_token"}, status=400)

        # 2) 사용자 정보
        try:
            info = fetch_userinfo(kakao_access_token)
        except Exception as e:
            return Response({"detail": f"userinfo failed: {e}"}, status=400)

        kakao_id = info.get("id")
        kakao_account = (info.get("kakao_account") or {})
        email = kakao_account.get("email")
        profile = kakao_account.get("profile") or {}
        nickname_from_kakao = profile.get("nickname")

        if not email:
            email = f"kakao_{kakao_id}@kakao.local"

        defaults = {"nickname": (nickname_from_kakao or email.split("@")[0])}
        user, _ = User.objects.get_or_create(email=email, defaults=defaults)

        # 3) 서비스 토큰 발급
        tokens = issue_tokens(user)

        # 4) 프런트 콜백 해시로 토큰 전달
        FRONT = getattr(settings, "FRONTEND_URL", "http://localhost:5173")
        access_q = quote_plus(tokens["access"])
        refresh_q = quote_plus(tokens["refresh"])
        
        return redirect(f"{FRONT}/oauth/callback#provider=kakao&access={access_q}&refresh={refresh_q}")
        
        # 쿠키 세팅 추가
        is_secure = not settings.DEBUG
        samesite = "None" if is_secure else "Lax"
        response.set_cookie("access", tokens["access"], httponly=True, secure=is_secure, samesite=samesite, path="/")
        response.set_cookie("refresh", tokens["refresh"], httponly=True, secure=is_secure, samesite=samesite, path="/")
        
        return response