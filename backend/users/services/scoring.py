from typing import Dict, List
from users.enums import RiskProfileChoices

# ----- 점수 테이블 -----
PRODUCT_SCORES = {
    "deposit": 0,
    "bond": 1,
    "stock_etf": 2,
    "fund": 2,
    "derivatives": 3,
    "overseas": 3,
}
HISTORY_PERIOD_SCORES = {"<1y": 0, "1-3y": 1, ">=3y": 2}
HISTORY_FREQ_SCORES = {"none": 0, "year_1_3": 1, "month_1plus": 2}
INCOME_SCORES = {"<30m": 0, "30_70m": 1, "70_100m": 2, ">=100m": 3}
WEALTH_SCORES = {"<50m": 0, "50_100m": 1, "100m_500m": 2, ">=500m": 3}
DEBT_SCORES = {"gte_50pct": 0, "30_50pct": 1, "10_30pct": 2, "lt_10pct": 3}
INVEST_SHARE_SCORES = {"<10pct": 3, "10_30pct": 2, "30_50pct": 1, ">=50pct": 0}
PURPOSE_SCORES = {
    "preservation": 0,
    "moderate": 2,
    "active": 3,
    "aggressive": 4,
}
TARGET_RETURN_SCORES = {"<=3": 0, "3_5": 1, "5_10": 2, ">=10": 3}
LOSS_RESPONSE_SCORES = {"sell_all": 0, "sell_partial": 1, "hold": 2, "buy_more": 3}
VOL_FEEL_SCORES = {"very_anxious": 0, "somewhat_anxious": 1, "ok": 2, "opportunity": 3}
LOSS_FOR_RETURN_SCORES = {"never": 0, "no": 1, "yes": 2, "strong_yes": 3}
HORIZON_SCORES = {"<1y": 0, "1_3y": 1, "3_5y": 2, ">=5y": 3}

# ----- 섹션 점수 -----
def calc_experience(payload: Dict) -> int:
    prods: List[str] = payload.get("products", [])
    prod_score = min(sum(PRODUCT_SCORES[p] for p in prods), 6)
    period_score = HISTORY_PERIOD_SCORES[payload["history_period"]]
    freq_score = HISTORY_FREQ_SCORES[payload["history_freq"]]
    return prod_score + period_score + freq_score  # max 10

def calc_capacity(payload: Dict) -> int:
    return (
        INCOME_SCORES[payload["income"]]
        + WEALTH_SCORES[payload["wealth"]]
        + DEBT_SCORES[payload["debt_ratio"]]
        + INVEST_SHARE_SCORES[payload["invest_share"]]
    )  # max 12

def calc_goal(payload: Dict) -> int:
    return PURPOSE_SCORES[payload["purpose"]] + TARGET_RETURN_SCORES[payload["target_return"]]  # max 7

def calc_attitude(payload: Dict) -> int:
    return (
        LOSS_RESPONSE_SCORES[payload["loss_response"]]
        + VOL_FEEL_SCORES[payload["volatility_feel"]]
        + LOSS_FOR_RETURN_SCORES[payload["loss_for_return"]]
    )  # max 9

def calc_horizon(payload: Dict) -> int:
    return HORIZON_SCORES[payload["horizon"]]  # max 3

# ----- 매핑 -----
def _map_score_to_profile(total_score: float) -> RiskProfileChoices:
    if total_score <= 25:
        return RiskProfileChoices.CONSERVATIVE
    elif total_score <= 45:
        return RiskProfileChoices.MODERATE_CONSERVATIVE
    elif total_score <= 65:
        return RiskProfileChoices.BALANCED
    elif total_score <= 80:
        return RiskProfileChoices.GROWTH
    else:
        return RiskProfileChoices.AGGRESSIVE

# ----- 최종 평가 -----
def evaluate_risk_profile(payload: Dict) -> Dict:
    experience_score = calc_experience(payload)
    capacity_score   = calc_capacity(payload)
    goal_score       = calc_goal(payload)
    attitude_score   = calc_attitude(payload)
    horizon_score    = calc_horizon(payload)

    total_score = round(
        (experience_score / 10) * 20
        + (capacity_score   / 12) * 20
        + (goal_score       /  7) * 20
        + (attitude_score   /  9) * 30
        + (horizon_score    /  3) * 10,
        2,
    )

    choice = _map_score_to_profile(total_score)
    return {
        "total_score": total_score,
        "profile": choice.value,          # e.g. "BALANCED"
        "profile_label": choice.label,    # e.g. "중립형"
        "section_scores": {
            "experience_score": experience_score,
            "capacity_score":   capacity_score,
            "goal_score":       goal_score,
            "attitude_score":   attitude_score,
            "horizon_score":    horizon_score,
        },
    }