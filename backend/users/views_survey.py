# users/views_survey.py
from __future__ import annotations

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from users.models import SurveyResult
from users.serializers import SurveyResultSerializer
from users.services.survey_service import save_survey_and_update_snapshot


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def survey_save(request):
    """
    POST /api/users/survey/save
      - body: 설문 원문 payload(JSON)
      - 동작: 점수 계산 → SurveyResult 저장 → 스냅샷 갱신
      - 응답: 방금 저장된 SurveyResult (201)
    """
    sr = save_survey_and_update_snapshot(request.user, request.data)
    return Response(SurveyResultSerializer(sr).data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def survey_current(request):
    """
    GET /api/users/survey/current
      - 현재(스냅샷) 설문 결과를 O(1)로 반환
      - 없으면 404
    """
    snap = getattr(request.user, "risk_snapshot", None)
    latest = getattr(snap, "latest_result", None) if snap else None
    if not latest:
        return Response({"detail": "no survey yet"}, status=status.HTTP_404_NOT_FOUND)
    return Response(SurveyResultSerializer(latest).data, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def survey_status(request):
    """
    GET /api/users/risk/status
      - 1차 설문(리스크 진단) 존재 여부만 반환
      - 응답 예:
        {
          "exists": true,
          "updated_at": "2025-12-17T12:34:56.000000Z",
          "profile": "BALANCED",
          "profile_label": "중립형"
        }
    """
    snap = getattr(request.user, "risk_snapshot", None)
    latest = getattr(snap, "latest_result", None) if snap else None

    exists = latest is not None
    updated_at = None
    profile = None
    profile_label = None

    if latest:
        ts = getattr(latest, "updated_at", None) or getattr(latest, "created_at", None)
        updated_at = ts.isoformat() if ts else None
        profile = getattr(latest, "profile", None)
        try:
            profile_label = latest.get_profile_display()
        except Exception:
            profile_label = None

    return Response(
        {
            "exists": exists,
            "updated_at": updated_at,
            "profile": profile,
            "profile_label": profile_label,
        },
        status=status.HTTP_200_OK,
    )