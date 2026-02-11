# analysis/serializers.py
from rest_framework import serializers
from portfolios.services.portfolio_rules import BUCKETS  # ✅ 올바른 경로
# 코드 → 한글 설명 맵(요청에 코드가 올 때 설명으로 정규화)
HORIZON_LABELS = {
    "LT_1Y":  "1년 이하 (단기)",
    "Y_1_3":  "1~3년 (중단기)",
    "Y_3_5":  "3~5년 (중기)",
    "GTE_5Y": "5년 이상 (장기)",
}

class RecommendInputSerializer(serializers.Serializer):
    amount_krw = serializers.IntegerField(min_value=1)
    # 두 키 중 하나만 와도 OK
    horizon = serializers.CharField(required=False, allow_blank=True)
    horizon_desc = serializers.CharField(required=False, allow_blank=True)
    must_buckets = serializers.ListField(
        child=serializers.ChoiceField(choices=BUCKETS),
        required=False,
        default=list,
    )

    def validate(self, attrs):
        # horizon(코드) 또는 horizon_desc(자유 텍스트) 중 하나는 필수
        raw = (attrs.get("horizon") or "").strip()
        desc = (attrs.get("horizon_desc") or "").strip()

        if not raw and not desc:
            raise serializers.ValidationError({"horizon": "horizon 또는 horizon_desc 중 하나는 필수입니다."})

        # 코드가 오면 라벨로 변환, 라벨이 오면 그대로 사용
        if raw:
            desc = HORIZON_LABELS.get(raw, raw)  # 코드가 아니면 그대로 텍스트 취급
        # 내부 표준 키로 정규화
        attrs["horizon_desc"] = desc
        attrs.pop("horizon", None)
        return attrs