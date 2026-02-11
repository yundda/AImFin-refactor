# users/views_google.py
from django.conf import settings
from django.shortcuts import redirect
from django.utils.crypto import get_random_string
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from urllib.parse import quote_plus

from .utils.pkce_store import save_verifier, pop_verifier, save_nonce, pop_nonce
from .utils.oauth_google import gen_pkce, build_auth_url, exchange_code_for_token
from .oauth_google_jwks import verify_id_token
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

def issue_tokens(user):
    r = RefreshToken.for_user(user)
    return {"access": str(r.access_token), "refresh": str(r)}

class GoogleStartView(APIView):
    def get(self, request):
        state = get_random_string(32)
        nonce = get_random_string(32)
        code_verifier, code_challenge = gen_pkce()
        save_verifier(state, code_verifier)
        save_nonce(state, nonce)
        url = build_auth_url(state, code_challenge) + f"&nonce={nonce}"
        return redirect(url)

class GoogleCallbackView(APIView):
    def get(self, request):
        code = request.query_params.get("code")
        state = request.query_params.get("state")
        if not code or not state:
            return Response({"detail": "missing code/state"}, status=400)

        code_verifier = pop_verifier(state)
        nonce = pop_nonce(state)
        if not code_verifier or not nonce:
            return Response({"detail": "invalid state/nonce"}, status=400)

        # 1) 코드→토큰
        try:
            token_json = exchange_code_for_token(code, code_verifier)
        except Exception as e:
            return Response({"detail": f"token exchange failed: {e}"}, status=400)

        id_token = token_json.get("id_token")
        access_token = token_json.get("access_token")
        if not id_token:
            return Response({"detail": "no id_token"}, status=400)

        # 2) 검증
        try:
            payload = verify_id_token(id_token, nonce=nonce, access_token=access_token)
        except Exception as e:
            return Response({"detail": f"id_token verify failed: {e}"}, status=400)

        email = payload.get("email") or f"google_{payload['sub']}@google.local"
        defaults = {"nickname": payload.get("name") or email.split("@")[0]}
        user, _ = User.objects.get_or_create(email=email, defaults=defaults)

        # 3) 서비스 토큰 발급
        tokens = issue_tokens(user)

        # 4) 프런트 콜백 해시로 토큰 전달 → 프런트가 localStorage 저장
        FRONT = getattr(settings, "FRONTEND_URL", "http://localhost:5173")
        access_q = quote_plus(tokens["access"])
        refresh_q = quote_plus(tokens["refresh"])
        
        return redirect(f"{FRONT}/oauth/callback#provider=google&access={access_q}&refresh={refresh_q}")
        
        # 쿠키 세팅 추가
        is_secure = not settings.DEBUG
        samesite = "None" if is_secure else "Lax"
        response.set_cookie("access", tokens["access"], httponly=True, secure=is_secure, samesite=samesite, path="/")
        response.set_cookie("refresh", tokens["refresh"], httponly=True, secure=is_secure, samesite=samesite, path="/")
        
        return response