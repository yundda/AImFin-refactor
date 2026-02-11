# analysis/services/compare.py
from __future__ import annotations
from typing import List, Dict, Any, Optional

from django.utils import timezone

from jsonschema import validate

from analysis.clients.gpt_client import complete_json
from analysis.services.metrics import compute_portfolio_metrics, risk_score_0_100
from analysis.prompts.util import render_prompt
from analysis.schemas.compare_response import COMPARE_RESPONSE_SCHEMA
from analysis.services.common import localize_text, labels_table_lines
from portfolios.services.portfolio_rules import get_universe_rules_for

# (선택) 포트폴리오 ID 로딩 지원
try:
    from portfolios.models import Portfolio
except Exception:  # 모델 경로/이름이 다를 수 있으니 안전하게
    Portfolio = None  # type: ignore


# ---------- 유틸 ----------

def _fmt_alloc_lines(allocs: List[Dict[str, Any]]) -> str:
    # [{"bucket":"STOCKS_KR","weight_pct":18}, ...] -> "- STOCKS_KR: 18.00%\n- ..."
    lines = []
    for a in allocs or []:
        b = a.get("bucket", "")
        w = float(a.get("weight_pct", 0.0))
        lines.append(f"- {b}: {w:.2f}%")
    return "\n".join(lines)

def _horizon_desc_for_user(user) -> str:
    pref = getattr(user, "investment_preference", None)
    code = getattr(pref, "horizon_code", None)
    mapping = {
        "LT_1Y": "1년 이하 (단기)",
        "Y_1_3": "1~3년 (중단기)",
        "Y_3_5": "3~5년 (중기)",
        "GTE_5Y": "5년 이상 (장기)",
    }
    return mapping.get(code, "기간 정보 없음")

def _risk_label_for_user(user) -> str:
    snap = getattr(user, "risk_snapshot", None)
    lr = getattr(snap, "latest_result", None)
    return lr.get_profile_display() if lr else "성향 정보 없음"

def _metrics_from_spec_or_compute(spec: Dict[str, Any], allocs: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    프론트가 리밸런싱 직후 '같은 수치'를 쓰고 싶다면 spec.metrics 를 같이 보내면 그 값을 그대로 사용.
    없으면 서버에서 계산.
    """
    m_in = spec.get("metrics")
    if isinstance(m_in, dict) and "expected_return_pct" in m_in and "risk_score" in m_in:
        # 들어온 값을 그대로(표시용 2자리 고정)
        er = float(m_in.get("expected_return_pct", 0.0))
        rs = float(m_in.get("risk_score", 0.0))
        return {
            "expected_return_pct": float(f"{er:.2f}"),
            "risk_score": float(f"{rs:.2f}"),
        }

    # 서버 계산
    m = compute_portfolio_metrics(allocs) or {}
    er = float(m.get("expected_return_pct", 0.0))
    
    # compare 측은 위험점수를 metrics.compute의 risk_score_0_100이 없을 수 있으니
    # 없으면 metrics.risk_score_0_100 함수로 계산
    if "risk_score_0_100" in m:
        rs = float(m["risk_score_0_100"])
    elif "risk_score" in m:
        rs = float(m["risk_score"])
    else:
        rs = float(risk_score_0_100(m))

    return {
        "expected_return_pct": float(f"{er:.2f}"),
        "risk_score": float(f"{rs:.2f}"),
    }

def _allocs_from_id(user, pid: int) -> List[Dict[str, Any]]:
    """
    포트폴리오 ID로부터 allocations를 꺼낸다.
    필드명이 프로젝트별로 다를 수 있어 다중 후보를 순회.
    """
    if not Portfolio:
        raise ValueError("Portfolio 모델을 찾을 수 없습니다.")
    p = Portfolio.objects.get(pk=pid, user=user)
    # 후보 필드들 중 먼저 나오는 것을 사용
    candidates = [
        getattr(p, "final_allocations", None),
        getattr(p, "allocations", None),
        getattr(p, "current_allocations", None),
        getattr(p, "buckets", None),
    ]
    for c in candidates:
        if isinstance(c, list) and c and isinstance(c[0], dict) and "bucket" in c[0]:
            return c
    raise ValueError("해당 포트폴리오에서 allocations 필드를 찾을 수 없습니다.")

def _resolve_side(user, spec: Dict[str, Any]) -> Dict[str, Any]:
    """
    spec -> {"allocs": [...], "metrics": {...}}
    - type: "id" | "allocations"
    - allocations: [{bucket, weight_pct}, ...]
    - metrics: {expected_return_pct, risk_score} (옵션, 주어지면 그대로 사용)
    """
    t = spec.get("type")
    if t == "id":
        pid = int(spec.get("id"))
        allocs = _allocs_from_id(user, pid)
        metrics = _metrics_from_spec_or_compute(spec, allocs)  # spec.metrics 가 있으면 그대로 사용
        return {"allocs": allocs, "metrics": metrics}
    elif t == "allocations":
        allocs = spec.get("allocations") or []
        metrics = _metrics_from_spec_or_compute(spec, allocs)
        return {"allocs": allocs, "metrics": metrics}
    else:
        raise ValueError("type 은 'id' 또는 'allocations' 이어야 합니다.")

def _build_compare_prompt(
    *,
    user,
    left_allocs: List[Dict[str, Any]],
    right_allocs: List[Dict[str, Any]],
    left_metrics: Dict[str, float],
    right_metrics: Dict[str, float],
) -> str:
    """
    - 좌/우 버킷 라인 + 좌/우 메트릭(프론트가 준 값이 있으면 그대로 사용)
    - 정책 요약(정책 자체는 참고 정보로만; 배분 판단은 프롬프트 규칙에 따름)
    - 사용자 맥락(성향 라벨, 투자기간 설명)
    """
    uni = get_universe_rules_for(user)  # policy_summary 용도
    policy_summary = uni.get("policy_summary", "")

    ctx = {
        "left_alloc_lines": _fmt_alloc_lines(left_allocs),
        "right_alloc_lines": _fmt_alloc_lines(right_allocs),
        "left_er_pct": f"{float(left_metrics.get('expected_return_pct', 0.0)):.2f}",
        "left_risk_score": f"{float(left_metrics.get('risk_score', 0.0)):.2f}",
        "right_er_pct": f"{float(right_metrics.get('expected_return_pct', 0.0)):.2f}",
        "right_risk_score": f"{float(right_metrics.get('risk_score', 0.0)):.2f}",
        "policy_summary": policy_summary,
        "risk_label": _risk_label_for_user(user),
        "horizon_desc": _horizon_desc_for_user(user),
        "bucket_labels_table": labels_table_lines(),
    }
    return render_prompt("compare_prompt.txt", ctx)


# ---------- 메인 ----------

def evaluate_comparison(
    *,
    user,
    left_allocations: List[Dict[str, Any]],
    right_allocations: List[Dict[str, Any]],
    left_spec: Optional[Dict[str, Any]] = None,
    right_spec: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    비교 분석 메인 엔트리.
    - 입력: 좌/우 버킷 비중(가중치 합=100 가정)
    - 출력: {"rationale": str, "summary": str, "risks": str, "generated_at": iso}
    """
    # 프론트가 metrics 를 같이 보낸 경우를 살리기 위해 spec을 넘겨받아 우선 사용
    l_metrics = _metrics_from_spec_or_compute(left_spec or {}, left_allocations)
    r_metrics = _metrics_from_spec_or_compute(right_spec or {}, right_allocations)

    prompt = _build_compare_prompt(
        user=user,
        left_allocs=left_allocations,
        right_allocs=right_allocations,
        left_metrics=l_metrics,
        right_metrics=r_metrics,
    )

    raw = complete_json(prompt, schema=COMPARE_RESPONSE_SCHEMA if COMPARE_RESPONSE_SCHEMA else None)
    if validate and COMPARE_RESPONSE_SCHEMA:
        try:
            validate(instance=raw, schema=COMPARE_RESPONSE_SCHEMA)
        except Exception:
            pass

    raw["rationale"] = localize_text(raw.get("rationale", ""))
    raw["summary"]   = localize_text(raw.get("summary", ""))
    raw["risks"]     = localize_text(raw.get("risks", ""))

    return {
        "rationale": raw.get("rationale", ""),
        "summary":   raw.get("summary", ""),
        "risks":     raw.get("risks", ""),
        "generated_at": timezone.now().isoformat(),
    }


def compare_portfolios(
    *,
    user,
    left_spec: Optional[Dict[str, Any]] = None,
    right_spec: Optional[Dict[str, Any]] = None,
    left_allocations: Optional[List[Dict[str, Any]]] = None,
    right_allocations: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    허용 인자:
    - left/right: {"type":"id","id":N} 또는 {"type":"allocations","allocations":[...], (opt) metrics:{...}}
    - 또는 left_allocations/right_allocations 를 직접 넘겨도 됨.
    """
    # spec 우선: metrics 동기화를 위해
    if left_spec is not None:
        l = _resolve_side(user, left_spec)
        left_allocations = l["allocs"]
        left_spec = {"metrics": l["metrics"], **(left_spec or {})}
    else:
        left_allocations = left_allocations or []

    if right_spec is not None:
        r = _resolve_side(user, right_spec)
        right_allocations = r["allocs"]
        right_spec = {"metrics": r["metrics"], **(right_spec or {})}
    else:
        right_allocations = right_allocations or []

    return evaluate_comparison(
        user=user,
        left_allocations=left_allocations or [],
        right_allocations=right_allocations or [],
        left_spec=left_spec,
        right_spec=right_spec,
    )