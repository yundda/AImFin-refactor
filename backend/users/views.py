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

User = get_user_model()

@api_view(["POST"])
def signup(request):
    ser = RegisterSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    ser.save()
    return Response(ser.data, status=status.HTTP_201_CREATED)

class CustomLoginView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        # 기본 JWT 발급(JSON: access/refresh)
        response = super().post(request, *args, **kwargs)

        # # 아래 쿠키 세팅은 남겨둬도 localStorage 방식에 지장 없음(프론트는 JSON만 사용)
        # access_token = response.data.get("access")
        # refresh_token = response.data.get("refresh")
        # if access_token and refresh_token:
        #     from django.conf import settings
        #     is_secure = not settings.DEBUG
        #     samesite = "None" if is_secure else "Lax"
        #     response.set_cookie("access", access_token, httponly=True, secure=is_secure, samesite=samesite, path="/")
        #     response.set_cookie("refresh", refresh_token, httponly=True, secure=is_secure, samesite=samesite, path="/")
        return response

class LogoutView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        refresh = request.data.get("refresh")
        if refresh:
            try:
                token = RefreshToken(refresh)
                token.blacklist()
            except TokenError:
                pass
            except Exception:
                pass
        resp = Response(status=status.HTTP_205_RESET_CONTENT)
        resp.delete_cookie("access")
        resp.delete_cookie("refresh")
        return resp

class CookieRefreshView(APIView):
    def post(self, request):
        from django.conf import settings
        refresh = request.COOKIES.get("refresh") or request.data.get("refresh")
        if not refresh:
            return Response({"detail": "no refresh"}, status=400)
        try:
            token = RefreshToken(refresh)
            new_access = str(token.access_token)
            new_refresh = str(token)
        except TokenError:
            return Response({"detail": "invalid refresh"}, status=401)

        is_secure = not settings.DEBUG
        samesite = "None" if is_secure else "Lax"
        resp = Response({"access": new_access, "refresh": new_refresh}, status=200)  # JSON도 함께 반환
        resp.set_cookie("access", new_access, httponly=True, samesite=samesite, secure=is_secure, path="/")
        resp.set_cookie("refresh", new_refresh, httponly=True, samesite=samesite, secure=is_secure, path="/")
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