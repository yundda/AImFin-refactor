# analysis/views_recommend.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers, status
from rest_framework.response import Response

from analysis.services.recommend import recommend_portfolio


class RecommendRequestSerializer(serializers.Serializer):
    amount_krw = serializers.IntegerField(min_value=1)
    horizon = serializers.ChoiceField(choices=["LT_1Y","Y_1_3","Y_3_5","GTE_5Y"])
    must_buckets = serializers.ListField(
        child=serializers.ChoiceField(
            choices=[
                "STOCKS_KR", "STOCKS_GLB",
                "BONDS_KR", "BONDS_GLB",
                "FUNDS", "ALTERNATIVES", "CASH",
            ]
        ),
        required=False,
        allow_empty=True,
    )
    # 선택: 사용자가 고른 버킷은 반드시 포함 + 필요시 AI가 버킷 추가 허용
    allow_ai_additions = serializers.BooleanField(required=False, default=False)

    @staticmethod
    def to_human_horizon(code: str) -> str:
        # 서비스 prompt 쪽에서 읽기 좋은 표현으로 매핑
        return {
        "LT_1Y":  "1년 이하 (단기)",
        "Y_1_3":  "1~3년 (중단기)",
        "Y_3_5":  "3~5년 (중기)",
        "GTE_5Y": "5년 이상 (장기)",
        }[code]


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def recommend(request):
    """
    POST /api/analysis/recommend/portfolio
    body:
    {
      "amount_krw": 20000000,
      "horizon": "Y_3_5",
      "must_buckets": ["STOCKS_KR","STOCKS_GLB","BONDS_KR"],
      "allow_ai_additions": true
    }
    """
    ser = RecommendRequestSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    v = ser.validated_data

    horizon_desc = RecommendRequestSerializer.to_human_horizon(v["horizon"])

    result = recommend_portfolio(
        user=request.user,
        amount_krw=v["amount_krw"],
        horizon_desc=horizon_desc,
        must_buckets=v.get("must_buckets", []),
        allow_ai_additions=v.get("allow_ai_additions", False),
    )
    return Response(result, status=status.HTTP_200_OK)
