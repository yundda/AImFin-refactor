# portfolios/services/portfolio_rules.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Literal, Optional, Set

from django.db.models import QuerySet

from assets.models import Asset
from assets.enums import AssetType  # "STOCKS_KR" 등 7개 버킷 enum(str)라고 가정
from users.models import RiskProfileCode, User  # CONSERVATIVE 등

# ✅ 공개용: 정규화된 버킷 문자열 목록 (검증/프롬프트/시리얼라이저 공통 기준)
BUCKETS: List[str] = [
    "STOCKS_KR", "STOCKS_GLB",
    "BONDS_KR", "BONDS_GLB",
    "ALTERNATIVES", "FUNDS", "CASH",
]

def bucket_str(b: AssetType | str) -> str:
    """Enum -> 'STOCKS_KR' 문자열; 이미 문자열이면 그대로."""
    try:
        return b.value  # Enum(str, Enum) 형태일 때
    except AttributeError:
        return str(b)

# ---- 프론트 설문에서 오는 "꼭 담고 싶은 상품" 코드(7개 선택지) ----
IncludeProduct = Literal[
    "DOMESTIC_STOCK", "GLOBAL_STOCK",
    "DOMESTIC_BOND", "GLOBAL_BOND",
    "ALTERNATIVE", "FUND_GLB_MULTI", "CASH_EQ"
]

# 설문 선택 → 7개 버킷으로 매핑
PRODUCT_TO_BUCKETS: Dict[IncludeProduct, List[AssetType]] = {
    "DOMESTIC_STOCK": [AssetType.STOCKS_KR],
    "GLOBAL_STOCK":   [AssetType.STOCKS_GLB],
    "DOMESTIC_BOND":  [AssetType.BONDS_KR],
    "GLOBAL_BOND":    [AssetType.BONDS_GLB],
    "ALTERNATIVE":    [AssetType.ALTERNATIVES],
    "FUND_GLB_MULTI": [AssetType.FUNDS],
    "CASH_EQ":        [AssetType.CASH],
}

# 운용기간 코드(1단계 Preference와 동일)
HorizonCode = Literal["LT_1Y", "Y_1_3", "Y_3_5", "GTE_5Y"]

@dataclass
class BucketRule:
    bucket: AssetType
    min: float
    max: float
    target: float

RuleTable = Dict[AssetType, BucketRule]


def _rule(b: AssetType, mn: float, mx: float, tgt: float) -> BucketRule:
    return BucketRule(bucket=b, min=mn, max=mx, target=tgt)


# ---- 리스크 성향별 기본 min/max/target (%) ----
BASE_RULES: Dict[RiskProfileCode, RuleTable] = {
    RiskProfileCode.CONSERVATIVE: {
        AssetType.STOCKS_KR:     _rule(AssetType.STOCKS_KR,     0,  10,  3),
        AssetType.STOCKS_GLB:    _rule(AssetType.STOCKS_GLB,    0,  10,  5),
        AssetType.BONDS_KR:      _rule(AssetType.BONDS_KR,     30,  70, 50),
        AssetType.BONDS_GLB:     _rule(AssetType.BONDS_GLB,    10,  30, 15),
        AssetType.ALTERNATIVES:  _rule(AssetType.ALTERNATIVES,  0,   5,  2),
        AssetType.FUNDS:         _rule(AssetType.FUNDS,         0,  10,  5),
        AssetType.CASH:          _rule(AssetType.CASH,         10,  30, 20),
    },
    RiskProfileCode.MODERATE_CONSERVATIVE: {
        AssetType.STOCKS_KR:     _rule(AssetType.STOCKS_KR,     5,  20, 10),
        AssetType.STOCKS_GLB:    _rule(AssetType.STOCKS_GLB,    5,  25, 12),
        AssetType.BONDS_KR:      _rule(AssetType.BONDS_KR,     25,  55, 35),
        AssetType.BONDS_GLB:     _rule(AssetType.BONDS_GLB,    10,  35, 18),
        AssetType.ALTERNATIVES:  _rule(AssetType.ALTERNATIVES,  0,  10,  5),
        AssetType.FUNDS:         _rule(AssetType.FUNDS,         0,  15,  8),
        AssetType.CASH:          _rule(AssetType.CASH,          2,  15,  7),
    },
    RiskProfileCode.BALANCED: {
        AssetType.STOCKS_KR:     _rule(AssetType.STOCKS_KR,    10,  35, 18),
        AssetType.STOCKS_GLB:    _rule(AssetType.STOCKS_GLB,   10,  35, 20),
        AssetType.BONDS_KR:      _rule(AssetType.BONDS_KR,     15,  40, 25),
        AssetType.BONDS_GLB:     _rule(AssetType.BONDS_GLB,     5,  25, 14),
        AssetType.ALTERNATIVES:  _rule(AssetType.ALTERNATIVES,  0,  12,  6),
        AssetType.FUNDS:         _rule(AssetType.FUNDS,         0,  15,  8),
        AssetType.CASH:          _rule(AssetType.CASH,          0,  10,  5),
    },
    RiskProfileCode.GROWTH: {
        AssetType.STOCKS_KR:     _rule(AssetType.STOCKS_KR,    20,  50, 30),
        AssetType.STOCKS_GLB:    _rule(AssetType.STOCKS_GLB,   20,  55, 35),
        AssetType.BONDS_KR:      _rule(AssetType.BONDS_KR,      0,  20, 10),
        AssetType.BONDS_GLB:     _rule(AssetType.BONDS_GLB,     0,  15,  8),
        AssetType.ALTERNATIVES:  _rule(AssetType.ALTERNATIVES,  0,  15, 10),
        AssetType.FUNDS:         _rule(AssetType.FUNDS,         0,  15,  5),
        AssetType.CASH:          _rule(AssetType.CASH,          0,  10,  2),
    },
    RiskProfileCode.AGGRESSIVE: {
        AssetType.STOCKS_KR:     _rule(AssetType.STOCKS_KR,    25,  65, 35),
        AssetType.STOCKS_GLB:    _rule(AssetType.STOCKS_GLB,   30,  70, 45),
        AssetType.BONDS_KR:      _rule(AssetType.BONDS_KR,      0,  10,  5),
        AssetType.BONDS_GLB:     _rule(AssetType.BONDS_GLB,     0,  10,  5),
        AssetType.ALTERNATIVES:  _rule(AssetType.ALTERNATIVES,  0,  20, 10),
        AssetType.FUNDS:         _rule(AssetType.FUNDS,         0,  10,  0),
        AssetType.CASH:          _rule(AssetType.CASH,          0,   5,  0),
    },
}


# ---- 내부 유틸/요약 ----
def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _apply_horizon_adjust(rules: RuleTable, horizon: Optional[HorizonCode]) -> None:
    if not horizon:
        return
    if horizon == "LT_1Y":
        # 단기: 주식 상한↓ 타깃↓, 현금 하한↑
        for b in (AssetType.STOCKS_KR, AssetType.STOCKS_GLB):
            r = rules[b]; r.max = _clamp(r.max - 20, 0, 100); r.target = _clamp(r.target - 10, 0, r.max)
        rules[AssetType.CASH].min = _clamp(rules[AssetType.CASH].min + 10, 0, 100)
    elif horizon == "Y_1_3":
        for b in (AssetType.STOCKS_KR, AssetType.STOCKS_GLB):
            r = rules[b]; r.max = _clamp(r.max - 10, 0, 100); r.target = _clamp(r.target - 5, 0, r.max)
        rules[AssetType.CASH].min = _clamp(rules[AssetType.CASH].min + 5, 0, 100)
    elif horizon == "GTE_5Y":
        # 장기: 주식 하한↑
        for b in (AssetType.STOCKS_KR, AssetType.STOCKS_GLB):
            r = rules[b]; r.min = _clamp(r.min + 5, 0, r.max)


def _apply_include_must_have(rules: RuleTable, include_products: List[IncludeProduct]) -> None:
    """
    사용자가 '꼭 담고 싶은' 상품을 체크했을 때 해당 버킷의 하한을 올려 최소 배정되도록 유도.
    """
    MUST_MIN = 3.0
    for p in include_products or []:
        for bucket in PRODUCT_TO_BUCKETS.get(p, []):
            r = rules[bucket]
            r.min = max(r.min, MUST_MIN)
            if r.target < r.min:
                r.target = r.min


def _ensure_min_le_max(rules: RuleTable) -> None:
    for r in rules.values():
        if r.min > r.max:
            r.min = r.max
        r.target = _clamp(r.target, r.min, r.max)


def _eligible_assets(bucket: AssetType) -> List[str]:
    qs: QuerySet[Asset] = Asset.objects.filter(asset_type=bucket, is_enabled=True)
    return list(qs.values_list("code", flat=True))


def policy_summary_text(rules: RuleTable) -> str:
    """프롬프트에 넣을 정책 요약 문자열(고정 순서: BUCKETS)"""
    lines = []
    for key in BUCKETS:
        r = rules[AssetType(key)]
        lines.append(f"- {key}: min {r.min:.2f}%, max {r.max:.2f}%, target {r.target:.2f}%")
    return "\n".join(lines)


def _selected_bucket_set(include_products: List[IncludeProduct]) -> Set[AssetType]:
    """
    설문 'include_products'를 AssetType 집합으로 변환.
    (사용자가 체크한 버킷들)
    """
    sel: Set[AssetType] = set()
    for p in include_products or []:
        for b in PRODUCT_TO_BUCKETS.get(p, []):
            sel.add(b)
    return sel


def _apply_lock_unselected(
    rules: RuleTable,
    allowed: Set[AssetType],
) -> None:
    """
    allowed 에 없는 버킷은 min/max/target=0으로 잠금.
    (서비스에서 lock_unselected=True 로 호출 시 적용)
    """
    for b, r in rules.items():
        if b not in allowed:
            r.min = 0.0
            r.max = 0.0
            r.target = 0.0


# ---- 외부 공개: 사용자별 정책 룰 집합 제공 ----
def get_universe_rules_for(
    user: User,
    *,
    lock_unselected: bool = False,
    whitelist: Optional[List[str]] = None,
) -> dict:
    """
    현재 사용자 스냅샷(리스크 성향) + 최신 선호(금액/기간/상품)
    → 버킷별 min/max/target + 편입 가능 자산 목록

    옵션:
      - lock_unselected=True  : '사용자 선택 버킷만' 허용(그 외 버킷은 min/max/target=0)
      - whitelist=['STOCKS_KR', ...] : 잠금 모드에서도 반드시 열어둘 버킷(예: must_buckets)
    """
    snap = getattr(user, "risk_snapshot", None)
    if not snap:
        raise ValueError("no risk snapshot (survey required)")

    profile: RiskProfileCode = snap.latest_result.profile  # type: ignore
    base: RuleTable = {k: BucketRule(v.bucket, v.min, v.max, v.target) for k, v in BASE_RULES[profile].items()}

    pref = getattr(user, "investment_preference", None)
    horizon: Optional[HorizonCode] = getattr(pref, "horizon_code", None)
    include: List[IncludeProduct] = list(getattr(pref, "include_products", []) or [])

    # 사용자 컨텍스트 반영
    _apply_horizon_adjust(base, horizon)
    _apply_include_must_have(base, include)
    _ensure_min_le_max(base)

    # 기본/확장 허용 버킷 목록(문자열)
    selected_set = _selected_bucket_set(include)
    allowed_default = [bucket_str(b) for b in selected_set]  # 사용자가 선택한 버킷만
    allowed_extended = BUCKETS[:]                             # 전체 7버킷

    # 선택잠금 모드: 선택하지 않은 버킷은 0%로 봉인
    if lock_unselected:
        allowed_assets: Set[AssetType] = set(selected_set)
        # 화이트리스트가 있으면 예외로 허용(문자열 → Enum)
        if whitelist:
            for s in whitelist:
                try:
                    allowed_assets.add(AssetType(s))
                except Exception:
                    pass
        _apply_lock_unselected(base, allowed_assets)
        _ensure_min_le_max(base)  # 최종 정합성 다시 보정

    # 반환용 버킷 상세
    buckets = []
    for b, r in base.items():
        buckets.append({
            "bucket": bucket_str(b),           # 문자열로 반환(프론트/프롬프트 일관)
            "min": round(r.min, 2),
            "max": round(r.max, 2),
            "target": round(r.target, 2),
            "eligible_assets": _eligible_assets(b),
        })

    return {
        "profile": profile,
        "horizon_code": horizon,
        "include_products": include,
        "buckets": buckets,
        "policy_summary": policy_summary_text(base),
        "rules": base,  # 내부에서 재활용할 수 있도록 원본 객체도 반환
        # ➕ 서비스에서 모드 선택에 쓰도록 제공
        "allowed_buckets_default": allowed_default,   # 기본: 사용자 선택 버킷
        "allowed_buckets_extended": allowed_extended, # 확장: 전체 7버킷
    }