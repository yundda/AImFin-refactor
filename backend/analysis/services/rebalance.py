# analysis/services/rebalance.py
from __future__ import annotations
from typing import List

from django.utils import timezone
from jsonschema import validate

from analysis.schemas.recommend_response import RECOMMEND_RESPONSE_SCHEMA
from analysis.schemas.comment_response import COMMENT_RESPONSE_SCHEMA  # ★추가
from analysis.clients.gpt_client import complete_json
from analysis.services.metrics import compute_portfolio_metrics, risk_score_0_100
from analysis.prompts.util import render_prompt
from analysis.services.common import localize_text, labels_table_lines

from portfolios.models import Portfolio


def _format_allocations_lines(allocs: List[dict]) -> str:
    lines = []
    for row in allocs or []:
        b = row.get("bucket")
        w = float(row.get("weight_pct", 0))
        lines.append(f"- {b}: {w:.2f}%")
    return "\n".join(lines)


def evaluate_rebalance(
    *,
    user,
    portfolio_id: int,
    allocations_input: List[dict],
) -> dict:
    """
    프런트에서 받은 allocations_input을 '그대로' 분석만 수행.
    - 정책/정규화/재분배 없음
    - GPT는 코멘트만 생성, allocations는 입력 그대로 복사해 출력하도록 프롬프트에서 강제
    - metrics는 서버에서 계산
    """
    # 포트폴리오 메타만 사용(정책 사용 안 함)
    p = Portfolio.objects.get(pk=portfolio_id, user=user)
    amount_krw = int(p.amount_krw)
    horizon_desc = p.horizon_desc
    must_buckets = list(p.must_buckets or [])
    risk_profile = p.profile
    risk_label = p.profile_label

    # 외부 프롬프트 템플릿 사용
    ctx = {
        "risk_profile": risk_profile,
        "risk_label": risk_label,
        "amount_krw": f"{amount_krw:,} KRW",
        "horizon_desc": horizon_desc,
        "must_buckets": ", ".join(must_buckets) if must_buckets else "없음",
        "current_allocations": _format_allocations_lines(allocations_input),
        "bucket_labels_table": labels_table_lines(),
    }
    prompt = render_prompt("rebalance_eval_prompt.txt", ctx)

    # GPT 호출 + 스키마 검증
    raw = complete_json(prompt, schema=RECOMMEND_RESPONSE_SCHEMA)
    try:
        validate(instance=raw, schema=RECOMMEND_RESPONSE_SCHEMA)
    except Exception:
        pass

    # 톤/라벨 로컬라이즈
    raw["rationale"] = localize_text(raw.get("rationale", ""))
    raw["summary"] = localize_text(raw.get("summary", ""))

    # 최종 비중 = 입력 그대로 (보정/정규화 없음)
    proposed = allocations_input
    final_with_assets = allocations_input
    notes: List[str] = []

    # 서버 지표 계산
    m_all = compute_portfolio_metrics(final_with_assets)
    expected_return_pct = float(f"{float(m_all.get('expected_return_pct', 0.0)):.2f}")
    risk_score = float(f"{risk_score_0_100(m_all):.2f}")

    final_lines = "\n".join([f"- {x['bucket']}: {float(x['weight_pct']):.2f}%" for x in final_with_assets])
    comment_ctx = {
        "final_alloc_lines": final_lines,
        "er_pct": f"{expected_return_pct:.2f}",
        "risk_score": f"{risk_score:.2f}",
        "risk_label": getattr(p, "profile_label", ""),  # 포트폴리오 라벨
        "horizon_desc": horizon_desc,
        "bucket_labels_table": labels_table_lines(),
    }
    comment_raw = complete_json(
        render_prompt("comment_from_final.txt", comment_ctx),
        schema=COMMENT_RESPONSE_SCHEMA
    )
    comment_raw["rationale"] = localize_text(comment_raw.get("rationale", ""))
    comment_raw["summary"]   = localize_text(comment_raw.get("summary", ""))

    return {
        # ...기존 응답 키 유지...
        "rationale": comment_raw.get("rationale", ""),
        "summary": comment_raw.get("summary", ""),
        "metrics": {
            "expected_return_pct": expected_return_pct,
            "risk_score": risk_score,
        },
        # ...생략...
    }