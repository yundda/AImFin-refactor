# analysis/views_compare.py
from __future__ import annotations
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from analysis.services.compare import compare_portfolios


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def compare_portfolio(request):
    """
    POST /api/analysis/compare/portfolio

    Body (세 모드 중 하나)
    1) {"left":{"type":"id","id":2}, "right":{"type":"id","id":5}}
    2) {"left":{"type":"id","id":2}, "right":{"type":"allocations","allocations":[...]}}
    3) {"left":{"type":"allocations","allocations":[...]}, "right":{"type":"allocations","allocations":[...]}}

    응답: {"rationale": str, "summary": str|[str], "risks": str}
    """
    left_spec = request.data.get("left")
    right_spec = request.data.get("right")
    if not left_spec or not right_spec:
        return Response({"detail": "left, right 둘 다 필요합니다."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        out = compare_portfolios(user=request.user, left_spec=left_spec, right_spec=right_spec)
        return Response(out, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)