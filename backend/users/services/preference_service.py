# users/services/preference_service.py
from typing import Dict, Any
from django.db import transaction
from ..models import (
    InvestmentPreference,
    UserPreferenceSnapshot,
    UserRiskSnapshot,
)
from ..serializers import InvestmentPreferenceCreateSerializer


@transaction.atomic
def save_preference_and_update_snapshot(user, payload: Dict[str, Any]) -> InvestmentPreference:
    """
    - payload 검증
    - InvestmentPreference 저장
    - UserPreferenceSnapshot 갱신
    """
    ser = InvestmentPreferenceCreateSerializer(data=payload)
    ser.is_valid(raise_exception=True)
    data = ser.validated_data

    # 최신 성향 설문과 연결(있으면)
    risk_snap = getattr(user, "risk_snapshot", None)
    from_survey = getattr(risk_snap, "latest_result", None) if risk_snap else None

    pref = InvestmentPreference.objects.create(
        user=user,
        amount_krw=data["amount_krw"],
        horizon_code=data["horizon_code"],
        include_products=data["include_products"],
        raw_payload=payload,
        from_survey=from_survey,
    )

    # 스냅샷 upsert
    UserPreferenceSnapshot.objects.update_or_create(
        user=user, defaults={"latest_pref": pref}
    )
    return pref