# analysis/services/recommend.py
from __future__ import annotations
from typing import Dict, List
from django.utils import timezone
from jsonschema import validate

from analysis.schemas.recommend_response import RECOMMEND_RESPONSE_SCHEMA
from analysis.schemas.comment_response import COMMENT_RESPONSE_SCHEMA  
from analysis.clients.gpt_client import complete_json
from analysis.services.metrics import compute_portfolio_metrics, risk_score_0_100
from analysis.prompts.util import render_prompt
from analysis.services.common import localize_text, labels_table_lines

from portfolios.services.portfolio_rules import get_universe_rules_for, BucketRule
from portfolios.services.policy import (
    reconcile_proposed_allocations,
    normalize_assets_within_bucket,
    apply_horizon_override,
    apply_selected_buckets_mode,   # ✅ 선택 버킷 모드 적용 (allow_ai_additions 반영)
)

# ---- 프롬프트 구성 -----------------------------------------------------------
def build_prompt(*, user, amount_krw: int, horizon_desc: str, must_buckets: list[str]) -> str:
    policy = get_universe_rules_for(user)
    eligible_lines = []
    for b in [r["bucket"] for r in policy["buckets"]]:
        eligible = next(x for x in policy["buckets"] if x["bucket"] == b)["eligible_assets"]
        eligible_lines.append(f"- {b}: [{', '.join(eligible)}]" if eligible else f"- {b}: []")

    ctx = {
        # 프롬프트는 위험 성향에 한글 라벨만 사용(하단 텍스트 파일 규칙과 일치)
        "risk_profile": policy["profile"],  # 필요 시 내부 참고용(프롬프트는 $risk_label만 사용)
        "risk_label": user.risk_snapshot.latest_result.get_profile_display(),
        "amount_krw": f"{amount_krw:,} KRW",
        "horizon_desc": horizon_desc,
        "must_buckets": must_buckets,
        "policy_summary": policy["policy_summary"],
        "eligible_assets_by_bucket": "\n".join(eligible_lines),
        "bucket_labels_table": labels_table_lines(),
    }
    return render_prompt("recommend_prompt.txt", ctx)

# ---- 로컬 헬퍼 ---------------------------------------------------------------
def _assets_fix_to_bucket(entry: dict) -> dict:
    """
    entry = {"bucket": "...", "weight_pct": float, "assets": [{code, weight_pct}, ...]}
    자산 리스트가 있으면 합이 정확히 bucket weight와 일치하도록 정규화.
    없으면 빈 배열로 통일.
    """
    assets = entry.get("assets") or []
    w = float(entry.get("weight_pct", 0.0))
    if not assets:
        return {"bucket": entry["bucket"], "weight_pct": float(round(w, 2)), "assets": []}
    fixed = normalize_assets_within_bucket(w, assets)
    return {"bucket": entry["bucket"], "weight_pct": float(round(w, 2)), "assets": fixed}

# ---- 메인 함수 ---------------------------------------------------------------
def recommend_portfolio(
    *,
    user,
    amount_krw: int,
    horizon_desc: str,
    must_buckets: List[str],
    allow_ai_additions: bool = False,   # True면 비선택 버킷 추가 허용
) -> dict:
    """
    - 사용자 최신 스냅샷으로 정책/유니버스 획득
    - GPT 제안 → 정책 집행(선택 버킷 모드/기간 오버라이드/정규화)
    - 서버 계산식으로 기대수익/위험점수 산출(둘만 노출)
    """

    # 1) 프롬프트
    prompt = build_prompt(
        user=user,
        amount_krw=amount_krw,
        horizon_desc=horizon_desc,
        must_buckets=must_buckets,
    )

    # 2) GPT 호출 + 스키마 검증 + 라벨 현지화
    raw = complete_json(prompt, schema=RECOMMEND_RESPONSE_SCHEMA)
    validate(instance=raw, schema=RECOMMEND_RESPONSE_SCHEMA)

    raw["rationale"] = localize_text(raw.get("rationale", ""))
    raw["summary"]   = localize_text(raw.get("summary", ""))

    # 3) 정책/유니버스
    uni = get_universe_rules_for(user)
    rules: Dict[str, BucketRule] = uni["rules"]

    # 3-1) 기간 오버라이드(유효 코드일 때만 반영)
    apply_horizon_override(rules, horizon_desc)

    # 3-2) 선택 버킷 모드 (사용자 선택만 허용 or AI 추가 허용)
    apply_selected_buckets_mode(rules, must_buckets, allow_ai_additions=allow_ai_additions)

    # 4) 정책 하에서 가중치 정규화
    proposed = raw.get("allocations", [])
    final_allocs, notes = reconcile_proposed_allocations(
        rules=rules,
        proposed_allocs=proposed,
    )

    # 5) 버킷 내부 종목 비중 정규화
    proposed_map = {a["bucket"]: a for a in proposed}
    final_with_assets = []
    for row in final_allocs:
        src = proposed_map.get(row["bucket"], {"assets": []})
        merged = {
            "bucket": row["bucket"],
            "weight_pct": row["weight_pct"],
            "assets": src.get("assets", []),
        }
        final_with_assets.append(_assets_fix_to_bucket(merged))

    # 6) 서버 계산식(metrics) → 기대수익/위험점수 두 값만 노출
    metrics_all = compute_portfolio_metrics(final_with_assets)
    expected_return_pct = float(f"{float(metrics_all.get('expected_return_pct', 0.0)):.2f}")
    risk_score = float(f"{float(risk_score_0_100(metrics_all)):.2f}")
    
    # 7) ★ 2차 호출: 최종안으로 코멘트 생성
    final_lines = "\n".join([f"- {x['bucket']}: {float(x['weight_pct']):.2f}%" for x in final_with_assets])
    comment_ctx = {
        "final_alloc_lines": final_lines,
        "er_pct": f"{expected_return_pct:.2f}",
        "risk_score": f"{risk_score:.2f}",
        "risk_label": user.risk_snapshot.latest_result.get_profile_display(),
        "horizon_desc": horizon_desc,
        "bucket_labels_table": labels_table_lines(),
    }
    comment_raw = complete_json(
        render_prompt("comment_from_final.txt", comment_ctx),
        schema=COMMENT_RESPONSE_SCHEMA
    )
    # 현지화(필요시)
    comment_raw["rationale"] = localize_text(comment_raw.get("rationale", ""))
    comment_raw["summary"]   = localize_text(comment_raw.get("summary", ""))

    # 8) 최종 응답(프론트엔드엔 final만 노출)
    snap = user.risk_snapshot.latest_result
    return {
        "profile": snap.profile,
        "profile_label": snap.get_profile_display(),
        "amount_krw": amount_krw,
        "horizon_desc": horizon_desc,
        "must_buckets": must_buckets,
        # "proposed_allocations": proposed,  # 필요시만 유지, 프론트엔드는 숨겨도 OK
        "final_allocations": final_with_assets,
        "corrections": notes,
        "rationale": comment_raw.get("rationale", ""),
        "summary": comment_raw.get("summary", ""),
        "metrics": {
            "expected_return_pct": expected_return_pct,
            "risk_score": risk_score,
        },
        "generated_at": timezone.now().isoformat(),
    }
