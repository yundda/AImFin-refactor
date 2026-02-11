# analysis/services/metrics.py
from __future__ import annotations
from math import sqrt
from typing import Dict, List
from assets.enums import AssetType

# ---- 가정(연율, %) ----
RISK_FREE_PCT = 2.0  # (기존 1.5 → 2.0)

MU_PCT = {  # 기대수익률(연, %)
    AssetType.STOCKS_KR:   10.5,   # (8.5 → 10.5) 공격적
    AssetType.STOCKS_GLB:  12.0,   # (9.0 → 12.0) 공격적
    AssetType.BONDS_KR:     2.0,   # (2.3 → 2.0)
    AssetType.BONDS_GLB:    2.5,   # (2.8 → 2.5)
    AssetType.ALTERNATIVES: 7.0,   # (6.0 → 7.0)
    AssetType.FUNDS:        5.5,   # (4.8 → 5.5)
    AssetType.CASH:         1.5,   # (2.0 → 1.5)
}

SIGMA_PCT = {  # 변동성(연, %)
    AssetType.STOCKS_KR:    22.0,  # (20 → 22)
    AssetType.STOCKS_GLB:   19.0,  # (18 → 19)
    AssetType.BONDS_KR:      6.0,  # (5 → 6)
    AssetType.BONDS_GLB:     7.0,  # (6 → 7)
    AssetType.ALTERNATIVES: 14.0,  # (12 → 14)
    AssetType.FUNDS:         9.0,  # (8 → 9)
    AssetType.CASH:          0.5,
}

# 상관계수 행렬(대칭). 없는 조합은 0으로 간주.
# 필요하면 실데이터로 교체하세요.
BASE_CORR: Dict[str, Dict[str, float]] = {
    AssetType.STOCKS_KR: {
        AssetType.STOCKS_KR: 1.00, AssetType.STOCKS_GLB: 0.80, AssetType.BONDS_KR: -0.10,
        AssetType.BONDS_GLB: -0.10, AssetType.ALTERNATIVES: 0.40, AssetType.FUNDS: 0.60, AssetType.CASH: -0.10,
    },
    AssetType.STOCKS_GLB: {
        AssetType.STOCKS_KR: 0.80, AssetType.STOCKS_GLB: 1.00, AssetType.BONDS_KR: -0.15,
        AssetType.BONDS_GLB: -0.15, AssetType.ALTERNATIVES: 0.45, AssetType.FUNDS: 0.60, AssetType.CASH: -0.10,
    },
    AssetType.BONDS_KR: {
        AssetType.STOCKS_KR: -0.10, AssetType.STOCKS_GLB: -0.15, AssetType.BONDS_KR: 1.00,
        AssetType.BONDS_GLB: 0.70,  AssetType.ALTERNATIVES: -0.05, AssetType.FUNDS: 0.10,  AssetType.CASH: 0.30,
    },
    AssetType.BONDS_GLB: {
        AssetType.STOCKS_KR: -0.10, AssetType.STOCKS_GLB: -0.15, AssetType.BONDS_KR: 0.70,
        AssetType.BONDS_GLB: 1.00,  AssetType.ALTERNATIVES: -0.05, AssetType.FUNDS: 0.10,  AssetType.CASH: 0.30,
    },
    AssetType.ALTERNATIVES: {
        AssetType.STOCKS_KR: 0.40, AssetType.STOCKS_GLB: 0.45, AssetType.BONDS_KR: -0.05,
        AssetType.BONDS_GLB: -0.05, AssetType.ALTERNATIVES: 1.00, AssetType.FUNDS: 0.30, AssetType.CASH: 0.00,
    },
    AssetType.FUNDS: {
        AssetType.STOCKS_KR: 0.60, AssetType.STOCKS_GLB: 0.60, AssetType.BONDS_KR: 0.10,
        AssetType.BONDS_GLB: 0.10, AssetType.ALTERNATIVES: 0.30, AssetType.FUNDS: 1.00, AssetType.CASH: 0.00,
    },
    AssetType.CASH: {
        AssetType.STOCKS_KR: -0.10, AssetType.STOCKS_GLB: -0.10, AssetType.BONDS_KR: 0.30,
        AssetType.BONDS_GLB: 0.30,  AssetType.ALTERNATIVES: 0.00, AssetType.FUNDS: 0.00, AssetType.CASH: 1.00,
    },
}

ORDER = [
    AssetType.STOCKS_KR, AssetType.STOCKS_GLB, AssetType.BONDS_KR, AssetType.BONDS_GLB,
    AssetType.ALTERNATIVES, AssetType.FUNDS, AssetType.CASH
]


def _as_asset_type(b) -> AssetType:
    """문자열 'STOCKS_KR' 등을 AssetType enum으로 안전 변환"""
    try:
        return AssetType(b)
    except Exception:
        # 이미 enum일 수도 있고, 이상값이면 그대로 둔다(아래 in-check로 필터)
        return b

def _get_w_from_allocs(final_allocs: List[dict]) -> Dict[str, float]:
    # {bucket(enum): weight(0~1)}  ← ★ enum 키로 통일
    w: Dict[AssetType, float] = {b: 0.0 for b in ORDER}
    for it in final_allocs:
        raw = it.get("bucket")
        if raw is None:
            continue
        b = _as_asset_type(raw)
        if b in w:  # enum 키만 반영
            w[b] = float(it.get("weight_pct", 0.0)) / 100.0
    return w

def _variance(w: Dict[str, float]) -> float:
    # Var = sum_i sum_j w_i w_j sigma_i sigma_j corr_ij
    var = 0.0
    for i in ORDER:
        for j in ORDER:
            wi, wj = w[i], w[j]
            si = SIGMA_PCT[i] / 100.0
            sj = SIGMA_PCT[j] / 100.0
            cij = BASE_CORR.get(i, {}).get(j, 0.0)
            var += wi * wj * si * sj * cij
    return var

def _return(w: Dict[str, float]) -> float:
    # E[R] = sum_i w_i * mu_i
    r = 0.0
    for i in ORDER:
        r += w[i] * (MU_PCT[i] / 100.0)
    return r

def _risk_level(vol_pct: float) -> str:
    if vol_pct < 10.0:
        return "LOW"
    if vol_pct < 18.0:
        return "MEDIUM"
    return "HIGH"

def compute_portfolio_metrics(final_allocations: List[dict]) -> dict:
    """
    입력: final_allocations = [{"bucket": "STOCKS_KR", "weight_pct": 25.0, "assets":[...]}...]
    출력: 결정론적 지표(metrics)
    """
    w = _get_w_from_allocs(final_allocations)

    er = _return(w)                 # in fraction
    vol = sqrt(_variance(w))        # in fraction
    rf = RISK_FREE_PCT / 100.0

    exp_ret_pct = round(er * 100.0, 2)
    vol_pct = round(vol * 100.0, 2)
    excess = max(er - rf, 0.0)
    sharpe = round(excess / vol, 3) if vol > 0 else 0.0

    # 간단 근사: 연 MDD ~ 2.5 * sigma (보수적 근사, 필요시 대체)
    mdd_pct = round(min(vol * 100.0 * 2.5, 100.0), 2)

    # 기여도(정보성): 기대수익 기여/분산 기여
    # 분산 기여: w_i * (Σ w)_i
    sigma = {b: SIGMA_PCT[b] / 100.0 for b in ORDER}
    Sw = {i: 0.0 for i in ORDER}
    for i in ORDER:
        for j in ORDER:
            Sw[i] += sigma[i] * sigma[j] * BASE_CORR.get(i, {}).get(j, 0.0) * w[j]
    var_total = _variance(w)

    contrib = {}
    for i in ORDER:
        ret_c = w[i] * (MU_PCT[i] / 100.0) * 100.0  # %p
        var_c = (w[i] * Sw[i]) / var_total * 100.0 if var_total > 0 else 0.0
        contrib[i] = {
            "return_contrib_pctp": round(ret_c, 2),   # 퍼센트 포인트 기여
            "variance_contrib_pct": round(var_c, 2),  # 총 분산 대비 %
        }

    return {
        "assumptions": {
            "risk_free_pct": RISK_FREE_PCT,
            "mu_pct": MU_PCT,
            "sigma_pct": SIGMA_PCT,
        },
        "expected_return_pct": exp_ret_pct,
        "volatility_pct": vol_pct,
        "sharpe_ratio": sharpe,
        "mdd_pct": mdd_pct,
        "risk_level": _risk_level(vol_pct),
        "bucket_contributions": contrib,
    }

def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))

def risk_score_0_100(metrics_full: dict) -> int:
    """
    변동성/낙폭(MDD) 기반 0~100 점수(높을수록 위험).
    경험적 기준:
      - vol 30% ≈ 위험 100, 0% ≈ 0
      - mdd 50% ≈ 위험 100, 0% ≈ 0
      - 가중치: vol 0.6, mdd 0.4
    """
    vol = float(metrics_full.get("volatility_pct", 0.0))  # %
    mdd = float(metrics_full.get("mdd_pct", 0.0))         # %
    vol_norm = _clamp(vol / 30.0, 0.0, 1.0)
    mdd_norm = _clamp(mdd / 50.0, 0.0, 1.0)
    score = (0.6 * vol_norm + 0.4 * mdd_norm) * 100.0
    return int(round(_clamp(score, 0.0, 100.0)))

def summarize_metrics(metrics_full: dict) -> dict:
    """
    프론트/DB에 노출할 최소 메트릭만 반환.
    - expected_return_pct: 소수 2자리
    - risk_score_0_100: 정수(0~100)
    """
    er = float(metrics_full.get("expected_return_pct", 0.0))
    return {
        "expected_return_pct": round(er, 2),
        "risk_score_0_100": risk_score_0_100(metrics_full),
    }
