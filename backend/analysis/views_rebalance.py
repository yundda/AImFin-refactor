# analysis/views_rebalance.py
from __future__ import annotations

from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from portfolios.models import Portfolio
from analysis.services.rebalance import evaluate_rebalance


def _basic_validate_allocations(allocs):
    """
    아주 기본적인 형태 검증:
    - 리스트/비어있지 않음
    - 각 row에 bucket/weight_pct 필수
    - 버킷 중복 금지
    - assets 합이 버킷 weight와 (있다면) 일치
    - 전체 합계 100.00(±0.01 허용)
    """
    if not isinstance(allocs, list) or not allocs:
        return "allocations must be a non-empty list"

    total = 0.0
    seen = set()

    for row in allocs:
        if not isinstance(row, dict):
            return "each allocation must be an object"
        if "bucket" not in row or "weight_pct" not in row:
            return "each allocation requires 'bucket' and 'weight_pct'"

        bucket = row["bucket"]
        if bucket in seen:
            return f"duplicate bucket: {bucket}"
        seen.add(bucket)

        try:
            w = float(row["weight_pct"])
        except Exception:
            return f"invalid weight_pct: {row.get('weight_pct')}"

        total += w

        assets = row.get("assets")
        if isinstance(assets, list) and assets:
            try:
                s = sum(float(a.get("weight_pct", 0)) for a in assets)
            except Exception:
                return f"invalid asset weight in bucket {bucket}"
            if abs(s - w) > 0.01:
                return f"assets sum {s:.2f} != bucket weight {w:.2f} for {bucket}"

    if abs(total - 100.0) > 0.01:
        return f"allocations total must be 100.00 (got {total:.2f})"

    return None


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def rebalance(request, portfolio_id: int):
    """
    POST /api/analysis/rebalance/portfolio/<int:portfolio_id>

    body 예시:
    {
      "allocations": [
        {"bucket":"STOCKS_KR","weight_pct":18.0,"assets":[...]},
        {"bucket":"STOCKS_GLB","weight_pct":20.0},
        ... // 합계 100.00
      ]
    }

    응답: recommend와 동일 스키마(JSON)
    """
    # 1) 소유권 확인
    portfolio = get_object_or_404(Portfolio, pk=portfolio_id, user=request.user)

    # 2) 입력 파싱/간단 검증
    allocations = request.data.get("allocations")

    err = _basic_validate_allocations(allocations)
    if err:
        return Response({"detail": err}, status=status.HTTP_400_BAD_REQUEST)

    # 3) 서비스 호출 (GPT 코멘트 + 정책 검증 + 서버 메트릭)
    result = evaluate_rebalance(
        user=request.user,
        portfolio_id=portfolio.id,
        allocations_input=allocations,
    )
    # result는 recommend와 동일 스키마를 반환하도록 구현되어 있어야 합니다.
    return Response(result, status=status.HTTP_200_OK)