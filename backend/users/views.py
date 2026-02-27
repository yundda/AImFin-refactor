# users/views.py
import re
from django.contrib.auth import get_user_model
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import status

from .serializers import RegisterSerializer
from .models import SurveyResult  # 설문 이력 카운트용

from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie

class GetCSRFTokenView(APIView):
    permission_classes = [permissions.AllowAny]
    
    @method_decorator(ensure_csrf_cookie)
    def get(self, request):
        # ensure_csrf_cookie 데코레이터가 응답에 csrftoken 쿠키를 강제로 포함시킴
        # HTTPONLY 설정 시에도 쿠키는 세팅되지만 JS로 접근 불가하므로 JSON으로도 전달
        return Response({"csrftoken": get_token(request)}, status=status.HTTP_200_OK)

User = get_user_model()

@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def signup(request):
    ser = RegisterSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    ser.save()
    return Response(ser.data, status=status.HTTP_201_CREATED)

class CustomLoginView(TokenObtainPairView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        access_token = response.data.get("access")
        refresh_token = response.data.get("refresh")
        
        if access_token and refresh_token:
            from django.conf import settings
            is_secure = not settings.DEBUG
            samesite = "None" if is_secure else "Lax"
            
            # 쿠키에 토큰 설정
            response.set_cookie("access", access_token, httponly=True, secure=is_secure, samesite=samesite, path="/")
            response.set_cookie("refresh", refresh_token, httponly=True, secure=is_secure, samesite=samesite, path="/")
            
            # JSON 바디에서 토큰 제거 (보안 강화 및 혼재 방지)
            del response.data["access"]
            del response.data["refresh"]
            response.data["message"] = "Login successful"
            
        return response

class LogoutView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        # 쿠키에서 리프레시 토큰 추출 시도
        refresh = request.COOKIES.get("refresh") or request.data.get("refresh")
        if refresh:
            try:
                token = RefreshToken(refresh)
                token.blacklist()
            except Exception:
                pass
        resp = Response({"message": "Logout successful"}, status=status.HTTP_200_OK)
        resp.delete_cookie("access")
        resp.delete_cookie("refresh")
        return resp

class CookieRefreshView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    def post(self, request):
        from django.conf import settings
        refresh = request.COOKIES.get("refresh")
        if not refresh:
            return Response({"detail": "No refresh token provided"}, status=401)
            
        try:
            token = RefreshToken(refresh)
            new_access = str(token.access_token)
            # 리프레시 토큰 회전(Rotation) 시 새로운 리프레시 토큰 발급 가능
            # 여기서는 Access만 새로 발급하거나 Rotation 설정에 따라 처리
            # 기본적으로 access만 새로 쿠키에 구워줌
        except TokenError:
            return Response({"detail": "Invalid refresh token"}, status=401)

        is_secure = not settings.DEBUG
        samesite = "None" if is_secure else "Lax"
        resp = Response({"message": "Token refreshed"}, status=200)
        resp.set_cookie("access", new_access, httponly=True, samesite=samesite, secure=is_secure, path="/")
        return resp

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        u = request.user
        snap = getattr(u, "risk_snapshot", None)
        sr = getattr(snap, "latest_result", None) if snap else None
        data = {
            "id": u.id,
            "email": u.email,
            "nickname": u.nickname or "",
            "survey_profile": sr.profile if sr else None,
            "survey_profile_label": sr.get_profile_display() if sr else None,
            "survey_total_score": float(sr.total_score) if sr else None,
            "last_survey_at": sr.created_at.isoformat() if sr else None,
            "survey_count": SurveyResult.objects.filter(user=u).count(),
            "needs_nickname": not bool((u.nickname or "").strip()),
            "has_survey": bool(sr),
        }
        return Response(data, status=status.HTTP_200_OK)

class NicknameView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        return Response({"nickname": request.user.nickname or ""}, status=status.HTTP_200_OK)
    def patch(self, request):
        nick = (request.data.get("nickname") or "").strip()
        if not nick:
            return Response({"detail": "nickname is required"}, status=status.HTTP_400_BAD_REQUEST)
        if len(nick) > 20:
            return Response({"detail": "nickname too long (max 20)"}, status=status.HTTP_400_BAD_REQUEST)
        if not re.fullmatch(r"[A-Za-z0-9가-힣 _.\-]{1,20}", nick):
            return Response({"detail": "invalid nickname (allowed: letters, digits, 한글, space, . _ -)"}, status=status.HTTP_400_BAD_REQUEST)
        user = request.user
        user.nickname = nick
        user.save(update_fields=["nickname"])
        return Response({"id": user.id, "email": user.email, "nickname": user.nickname}, status=status.HTTP_200_OK)