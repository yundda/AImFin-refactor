# portfolios/services/policy.py
from __future__ import annotations
from typing import Dict, List, Tuple

from assets.enums import AssetType
from portfolios.services.portfolio_rules import BucketRule, RuleTable


def _round_int(x: float) -> int:
    return int(round(x))


def _round_2(x: float) -> float:
    return float(round(x, 2))


def _largest_remainder_to_100(
    values: Dict[AssetType, float],
    allowed: List[AssetType] | None = None,
) -> Dict[AssetType, float]:
    """
    실수 합을 정확히 100.00으로 만드는 라운딩(최대잔여 방식, 소수점 2자리).
    내부적으로 10000(100.00 * 100)을 기준으로 계산.
    """
    # 1) 스케일링 (100 -> 10000)
    SCALE = 100
    scaled_values = {k: v * SCALE for k, v in values.items()}
    
    # 2) 내림(정수) 기저
    floored = {k: int(scaled_values[k]) for k in scaled_values}

    allowed_set = set(allowed) if allowed is not None else None

    # 3) 잔여 계산 대상(allowed 한정)만 선정
    remainders: List[Tuple[AssetType, float]] = []
    for k, v in scaled_values.items():
        if (allowed_set is None) or (k in allowed_set):
            remainders.append((k, v - floored[k]))

    target_total = 100 * SCALE
    current_total = sum(floored.values())
    diff = target_total - current_total
    
    remainders.sort(key=lambda x: x[1], reverse=True)

    res = floored.copy()
    i, n = 0, len(remainders)
    while diff > 0 and n > 0:
        k, _ = remainders[i]
        res[k] += 1
        diff -= 1
        i = (i + 1) % n

    # 4) allowed 외는 0으로 강제
    if allowed_set is not None:
        for k in values:
            if k not in allowed_set:
                res[k] = 0

    # 5) 스케일링 복원
    return {k: float(v) / SCALE for k, v in res.items()}


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _waterfill_to_limits(
    rules: RuleTable,
    proposed: Dict[AssetType, float],
) -> Dict[AssetType, float]:
    """
    - 시작: 각 버킷을 '하한(min)'으로 초기화
    - 잔여(100 - sum(min))를 '희망 증가량(proposed_clamped - min)' 비율대로 물붓기(water-filling)
    - 상한(max) 도달 버킷은 고정하고 나머지에게 재분배(포화 반복)
    """
    mins = {b: r.min for b, r in rules.items()}
    maxs = {b: r.max for b, r in rules.items()}
    base = mins.copy()  # 현재 할당

    total_min = sum(mins.values())
    total_min = sum(mins.values())
    total_min = _round_int(total_min)
    if total_min > 100:
        # 정책이 과도하게 타이트한 경우: min을 균등비로 축소
        scale = 100.0 / total_min
        for b in base:
            base[b] = _round_int(base[b] * scale)
        return _largest_remainder_to_100(base)

    # 제안치 클리핑
    proposed_clamped = {b: _clamp(proposed.get(b, 0.0), mins[b], maxs[b]) for b in rules}

    remaining = 100.0 - total_min
    remaining = max(0.0, remaining)

    # 희망 증가량 = 제안치 - min (음수면 0)
    desire = {b: max(0.0, proposed_clamped[b] - mins[b]) for b in rules}
    capacity = {b: max(0.0, maxs[b] - mins[b]) for b in rules}

    active = set(rules.keys())
    alloc_extra = {b: 0.0 for b in rules}

    while remaining > 1e-9 and active:
        desire_sum = sum(desire[b] for b in active)
        if desire_sum <= 1e-9:
            # 더 원하는 곳이 없으면 target 기준으로 배분
            target_bias = {b: max(0.0, rules[b].target - mins[b]) for b in active}
            bias_sum = sum(target_bias.values()) or len(active)
            for b in list(active):
                add = remaining * (target_bias.get(b, 1.0) / bias_sum)
                add = min(add, capacity[b] - alloc_extra[b])
                alloc_extra[b] += add
                if abs(alloc_extra[b] - capacity[b]) < 1e-9:
                    active.remove(b)
            break

        for b in list(active):
            share = remaining * (desire[b] / desire_sum)
            share = min(share, capacity[b] - alloc_extra[b])
            alloc_extra[b] += share
            if abs(alloc_extra[b] - capacity[b]) < 1e-9:
                active.remove(b)

        remaining = 100.0 - sum(mins[b] + alloc_extra[b] for b in rules)

        # 남은 값이 음수/미세 오차면 정리
        if remaining < 0:
            remaining = 0.0

    result = {b: mins[b] + alloc_extra[b] for b in rules}
    # 마지막 100.00 보장 라운딩
    return _largest_remainder_to_100(result)


def reconcile_proposed_allocations(
    rules: RuleTable,
    proposed_allocs: List[dict],
) -> Tuple[List[dict], List[str]]:
    """
    GPT 제안(proposed_allocs [{bucket, weight_pct}, ...])을
    정책(min/max) 내에서 100.00%로 정규화하고, 조정 내역 메모를 반환.
    """
    notes: List[str] = []
    proposed_map: Dict[AssetType, float] = {a["bucket"]: float(a.get("weight_pct", 0.0)) for a in proposed_allocs}

    # 룰에 없는 버킷 제안은 무시
    for b in list(proposed_map.keys()):
        if b not in rules:
            notes.append(f"unknown bucket dropped: {b}")
            proposed_map.pop(b, None)

    # 빠진 버킷은 0으로 채워 넣기(룰은 항상 7버킷을 가짐)
    for b in rules:
        proposed_map.setdefault(b, 0.0)

    # --- min/max 초과/미달 사전 체크(정보만) ---
    for b, r in rules.items():
        v = proposed_map[b]
        if v < r.min:
            notes.append(f"{b} raised to min {r.min:.2f} from {v:.2f}")
        if v > r.max:
            notes.append(f"{b} clipped to max {r.max:.2f} from {v:.2f}")

    # --- NEW: 타깃 근접 유도를 위한 부드러운 블렌딩 ---
    # 타깃과 50:50로 섞어 과도한 극단값을 완화(시그니처 변경 없음)
    BLEND = 0.8  # 0~1 (값이 클수록 GPT 제안 가중)
    target_map: Dict[AssetType, float] = {b: rules[b].target for b in rules}
    blended_map: Dict[AssetType, float] = {
        b: BLEND * proposed_map[b] + (1 - BLEND) * target_map[b]
        for b in rules
    }

    # --- 물붓기로 min/max 내부에서 100.00 맞춤 ---
    adjusted_map = _waterfill_to_limits(rules, blended_map)
    adjusted_map = _largest_remainder_to_100(adjusted_map)

    final_allocs = [{"bucket": b, "weight_pct": adjusted_map[b]} for b in rules]
    final_allocs.sort(key=lambda x: x["bucket"])  # 안정적 출력

    notes.append("normalized to 100.00 (target-blended)")
    return final_allocs, notes

def normalize_assets_within_bucket(
    bucket_weight: float,
    assets: List[dict],
) -> List[dict]:
    """
    버킷 내부 종목 가중치의 합을 bucket_weight와 정확히 맞춤(소수점 2자리).
    assets = [{"code": "AAA", "weight_pct": 10.0}, ...]
    """
    if not assets:
        return []

    # 1) 비중이 0이면 빈 배열
    if bucket_weight <= 0:
        return []

    # 2) 단순 스케일링
    total = sum(float(a.get("weight_pct", 0.0)) for a in assets)
    if total <= 0:
        # 균등 분배
        equal = bucket_weight / len(assets)
        raw = [equal for _ in assets]
    else:
        scale_factor = bucket_weight / total
        raw = [float(a.get("weight_pct", 0.0)) * scale_factor for a in assets]

    # 3) Largest Remainder (Scale=100)
    SCALE = 100
    bucket_target_int = int(round(bucket_weight * SCALE))
    
    # 각 자산을 스케일링 후 내림
    raw_scaled = [val * SCALE for val in raw]
    floored = [int(val) for val in raw_scaled]
    
    current_sum = sum(floored)
    needed = bucket_target_int - current_sum
    
    # 잔여분(소수점 오차) 정렬
    rema = [(i, raw_scaled[i] - floored[i]) for i in range(len(raw))]
    rema.sort(key=lambda x: x[1], reverse=True)

    res = floored[:]
    idx = 0
    while needed > 0 and idx < len(res):
        res[rema[idx][0]] += 1
        needed -= 1
        idx = (idx + 1) if (idx + 1) < len(res) else 0

    out = []
    for i, a in enumerate(assets):
        # 스케일링 복원
        w_float = float(res[i]) / SCALE
        out.append({"code": a["code"], "weight_pct": w_float})
    return out

# --- 선택 버킷 보장/모드 적용 -----------------------------------------------
def apply_selected_buckets_mode(
    rules: RuleTable,
    selected_buckets: list[str] | None,
    *,
    allow_ai_additions: bool = False,
    must_min_pct: float = 3.0,
) -> None:
    """
    - selected_buckets: 사용자가 고른 버킷 문자열 목록
    - allow_ai_additions=False: 비선택 버킷은 max=0으로 봉인
    - allow_ai_additions=True: 비선택 버킷 열어두되, 선택 버킷은 0% 불가(min>=must_min_pct)
    """
    if not selected_buckets:
        return

    selected: set[AssetType] = set()
    for s in selected_buckets:
        try:
            selected.add(AssetType(s))
        except Exception:
            pass

    for b, r in rules.items():
        if b in selected:
            if r.min < must_min_pct:
                r.min = must_min_pct
            if r.target < r.min:
                r.target = r.min
        else:
            if not allow_ai_additions:
                r.min = 0.0
                r.max = 0.0
                r.target = 0.0


# --- 외부에서 기간 오버라이드할 때 사용 --------------------------------------
def apply_horizon_override(rules: RuleTable, horizon_code: str | None) -> None:
    """
    get_universe_rules_for()로 받은 rules에 기간 코드를 외부에서 강제로 반영.
    """
    from .portfolio_rules import _apply_horizon_adjust, _ensure_min_le_max  # 내부 유틸 재사용
    if not horizon_code:
        return
    _apply_horizon_adjust(rules, horizon_code)  # type: ignore[arg-type]
    _ensure_min_le_max(rules)
