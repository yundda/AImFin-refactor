from django.db import transaction
from django.utils.timezone import now

from users.models import SurveyResult, UserRiskSnapshot, RiskProfileCode
from users.services.scoring import evaluate_risk_profile  # 네가 만든 scoring.py
# evaluate_risk_profile(payload: dict) -> {
#   "total_score": float,
#   "profile": "CONSERVATIVE" | ...,
#   "section_scores": {
#       "experience_score": int,
#       "capacity_score": int,
#       "goal_score": int,
#       "attitude_score": int,
#       "horizon_score": int,
#   }
# }

@transaction.atomic
def save_survey_and_update_snapshot(user, survey_payload: dict) -> SurveyResult:
    """설문 원문으로 점수 계산 → SurveyResult 저장 → 스냅샷 갱신"""
    result = evaluate_risk_profile(survey_payload)

    sr = SurveyResult.objects.create(
        user=user,
        survey_json=survey_payload,
        total_score=result["total_score"],
        profile=result["profile"],             # RiskProfileCode 값이어야 함
        section_scores=result["section_scores"]
    )

    UserRiskSnapshot.objects.update_or_create(
        user=user,
        defaults={"latest_result": sr}
    )
    return sr


def score_to_profile(total_score: float) -> RiskProfileCode:
    """
    0~100 점수 가정. 경계는 필요에 맞게 미세조정 가능.
    """
    s = float(total_score)
    if s < 35:
        return RiskProfileCode.CONSERVATIVE
    if s < 50:
        return RiskProfileCode.MODERATE_CONSERVATIVE
    if s < 65:
        return RiskProfileCode.BALANCED
    if s < 82:
        return RiskProfileCode.GROWTH
    return RiskProfileCode.AGGRESSIVE  # ← 상단 경계 확실히 연다