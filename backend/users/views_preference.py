# users/views_preference.py
from __future__ import annotations

from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .serializers import (
    InvestmentPreferenceCreateSerializer,
    InvestmentPreferenceSerializer,
)
from .services.preference_service import save_preference_and_update_snapshot


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def preference_save(request):
    """
    POST /api/users/preference/save
      - body: { amount_krw, horizon_code, include_products: string[] }
      - return: 저장된 InvestmentPreference (201)
    """
    # (선택) 요청 검증을 원하면 주석 해제
    # s = InvestmentPreferenceCreateSerializer(data=request.data)
    # s.is_valid(raise_exception=True)
    pref = save_preference_and_update_snapshot(request.user, request.data)
    return Response(InvestmentPreferenceSerializer(pref).data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def preference_current(request):
    """
    GET /api/users/preference/current
      - return: 최신 InvestmentPreference (스냅샷)
      - 없으면 404
    """
    snap = getattr(request.user, "preference_snapshot", None)
    latest = getattr(snap, "latest_pref", None) if snap else None
    if not latest:
        return Response({"detail": "no preference yet"}, status=status.HTTP_404_NOT_FOUND)
    return Response(InvestmentPreferenceSerializer(latest).data, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def preference_status(request):
    """
    GET /api/users/preference/status
      - 2차 설문(선호 스냅샷) 존재 여부만 반환
      - 응답: { "exists": bool, "updated_at": ISO8601|null }
    """
    snap = getattr(request.user, "preference_snapshot", None)
    latest = getattr(snap, "latest_pref", None) if snap else None

    exists = latest is not None
    updated_at = None
    if latest:
        ts = getattr(latest, "updated_at", None) or getattr(latest, "created_at", None)
        if ts:
            updated_at = ts.isoformat()

    return Response(
        {"exists": exists, "updated_at": updated_at},
        status=status.HTTP_200_OK,
    )
from .models import UserMarketPreference
from .serializers import UserMarketPreferenceSerializer

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def market_preference_get(request):
    """
    GET /api/users/preference/market
    """
    pref, _ = UserMarketPreference.objects.get_or_create(user=request.user)
    return Response(UserMarketPreferenceSerializer(pref).data, status=status.HTTP_200_OK)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def market_preference_update(request):
    """
    POST /api/users/preference/market
    body: { "indices": ["KS11", "AAPL", ...] }
    """
    pref, _ = UserMarketPreference.objects.get_or_create(user=request.user)
    serializer = UserMarketPreferenceSerializer(pref, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
