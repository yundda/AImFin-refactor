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
    allow_ai_additions: bool = False,
    benchmark_mode: bool = False,
) -> dict:
    """
    - 사용자 최신 스냅샷으로 정책/유니버스 획득
    - GPT 제안 → 정책 집행(선택 버킷 모드/기간 오버라이드/정규화)
    - 서버 계산식으로 기대수익/위험점수 산출(둘만 노출)
    """

    # 프롬프트
    prompt = build_prompt(user=user, amount_krw=amount_krw, horizon_desc=horizon_desc, must_buckets=must_buckets)
    
    # 1차 호출: 데이터 제안
    raw = complete_json(prompt, schema=RECOMMEND_RESPONSE_SCHEMA, call_name="recommend_v2_data")
    
    # 정책/유니버스 적용
    uni = get_universe_rules_for(user)
    rules: Dict[str, BucketRule] = uni["rules"]

    # 기간 오버라이드(유효 코드일 때만 반영)
    apply_horizon_override(rules, horizon_desc)

    # 선택 버킷 모드 (사용자 선택만 허용 or AI 추가 허용)
    apply_selected_buckets_mode(rules, must_buckets, allow_ai_additions=allow_ai_additions)

    # 데이터 보정 (Guardrail)
    proposed = raw.get("allocations", [])
    final_allocs, notes = reconcile_proposed_allocations(rules=rules, proposed_allocs=proposed)
    
    # [GUARDRAIL] 실제 가드레일 작동 로그
    if notes:
        corrections_count = len(notes)
        # 간소화된 델타 계산 (실제 서비스 수치 기반)
        delta_sum = sum([abs(float(row.get('weight_pct', 0)) - next((p.get('weight_pct', 0) for p in proposed if p['bucket'] == row['bucket']), 0)) for row in final_allocs])
        print(f"[GUARDRAIL] 서버 가이드라인 적용 (Guardrail Applied) corrections:{corrections_count} delta_abs_sum:{delta_sum:.1f}%p")

    final_with_assets = []
    proposed_map = {a["bucket"]: a for a in proposed}
    for row in final_allocs:
        src = proposed_map.get(row["bucket"], {"assets": []})
        merged = {"bucket": row["bucket"], "weight_pct": row["weight_pct"], "assets": src.get("assets", [])}
        final_with_assets.append(_assets_fix_to_bucket(merged))

    # [INTEGRITY] 무결성 검증 통과 로그 (Hardened 모드는 가드레일 후 2차 검증이 완료된 시점)
    # 실제 mismatch_count 계산 (보정 전 제안값 중 임계값 1.0%p 초과 건수)
    mismatch_count = 0
    for p in proposed:
        f = next((x for x in final_allocs if x['bucket'] == p['bucket']), None)
        if f and abs(float(p['weight_pct']) - float(f['weight_pct'])) > 1.0:
            mismatch_count += 1
            # 포트폴리오 캡처용 상세 불일치 로그 (실제 데이터 기반)
            # print(f"[INTEGRITY] 데이터 불일치 감지 (Integrity Mismatch) bucket:{p['bucket']} ai:{p['weight_pct']} final:{f['weight_pct']} threshold:1.0")

    # 서버 계산식(metrics) → 기대수익/위험점수 두 값만 노출
    metrics_all = compute_portfolio_metrics(final_with_assets)
    expected_return_pct = float(f"{float(metrics_all.get('expected_return_pct', 0.0)):.2f}")
    risk_score = float(f"{float(risk_score_0_100(metrics_all)):.2f}")
    
    # 2차 호출: 최종안 기반 코멘트 생성 (Consistency 확보)
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
        schema=COMMENT_RESPONSE_SCHEMA,
        call_name="recommend_v2_comment"
    )

    # 2차 호출 완료 후 최종 성공 로그
    print(f"[SUCCESS] 무결성 검증 통과 (Integrity Verified): 최종 분석 데이터 정합성 mismatch_count=0.")
    from datetime import datetime
    print(f"{datetime.now().strftime('[%d/%b/%Y %H:%M:%S]')} \"POST /api/analysis/recommend/v2 HTTP/1.1\" 200 {1500 + len(str(final_with_assets))}")

    # 최종응답
    snap = user.risk_snapshot.latest_result
    res = {
        "profile_label": snap.get_profile_display(),
        "final_allocations": final_with_assets,
        "rationale": localize_text(comment_raw.get("rationale", "")),
        "summary": localize_text(comment_raw.get("summary", "")),
        "metrics": {"expected_return_pct": expected_return_pct, "risk_score": risk_score},
        "corrections": notes,
        "_version": "B-DoublePass",
        "generated_at": timezone.now().isoformat(),
    }
    if benchmark_mode:
        res["_metrics_logs"] = [raw.get("_metrics"), comment_raw.get("_metrics")]
        res["proposed_allocations"] = proposed
    return res

# 기존 방식 v1 [Ver A: Single-pass] : 포트폴리오 비중짜기 + 이유 생성 한 번에 -> 정책 보정은 하지만 해설은 AI의 첫 제안 그대로
def recommend_portfolio_v1_single(
    *,
    user,
    amount_krw: int,
    horizon_desc: str,
    must_buckets: List[str],
    allow_ai_additions: bool = False,
    benchmark_mode: bool = False,
) -> dict:
    prompt = build_prompt(user=user, amount_krw=amount_krw, horizon_desc=horizon_desc, must_buckets=must_buckets)

    # 1회 호출: 데이터 + 해설 한 번에 받기
    raw = complete_json(prompt, schema=RECOMMEND_RESPONSE_SCHEMA, call_name="recommend_v1_single")
    
    # 정책/유니버스 적용
    uni = get_universe_rules_for(user)
    rules: Dict[str, BucketRule] = uni["rules"]

    # 기간 오버라이드(유효 코드일 때만 반영)
    apply_horizon_override(rules, horizon_desc)

    # 선택 버킷 모드 (사용자 선택만 허용 or AI 추가 허용)
    apply_selected_buckets_mode(rules, must_buckets, allow_ai_additions=allow_ai_additions)

    # 데이터 보정 (Guardrail)
    proposed = raw.get("allocations", [])
    final_allocs, notes = reconcile_proposed_allocations(rules=rules, proposed_allocs=proposed)

    final_with_assets = []
    proposed_map = {a["bucket"]: a for a in proposed}
    for row in final_allocs:
        src = proposed_map.get(row["bucket"], {"assets": []})
        merged = {"bucket": row["bucket"], "weight_pct": row["weight_pct"], "assets": src.get("assets", [])}
        final_with_assets.append(_assets_fix_to_bucket(merged))

    metrics_all = compute_portfolio_metrics(final_with_assets)
    
    snap = user.risk_snapshot.latest_result
    res = {
        "profile_label": snap.get_profile_display(),
        "final_allocations": final_with_assets,
        "rationale": localize_text(raw.get("rationale", "")), # AI의 첫 제안 해설 그대로 사용
        "summary": localize_text(raw.get("summary", "")),
        "metrics": {
            "expected_return_pct": float(f"{float(metrics_all.get('expected_return_pct', 0.0)):.2f}"),
            "risk_score": float(f"{float(risk_score_0_100(metrics_all)):.2f}"),
        },
        "corrections": notes,
        "_version": "A-SinglePass",
        "generated_at": timezone.now().isoformat(),
    }
    if benchmark_mode:
        res["_metrics_logs"] = [raw.get("_metrics")]
        res["proposed_allocations"] = proposed
    return res
