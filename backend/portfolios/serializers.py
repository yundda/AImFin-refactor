# portfolios/serializers.py

from __future__ import annotations
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Any

from django.db import transaction
from rest_framework import serializers

from portfolios.models import Portfolio
from assets.enums import AssetType
from assets.models import Asset

try:
    from analysis.services.metrics import compute_portfolio_metrics, risk_score_0_100
except Exception:  # pragma: no cover
    compute_portfolio_metrics = None
    risk_score_0_100 = None


def q2f(x: float | int | Decimal | None) -> float:
    if x is None:
        return 0.0
    d = Decimal(str(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return float(d)


class PortfolioAssetInSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=32)
    weight_pct = serializers.FloatField(min_value=0.0)


class PortfolioAllocationInSerializer(serializers.Serializer):
    bucket = serializers.ChoiceField(choices=AssetType.choices)
    weight_pct = serializers.FloatField(min_value=0.0)
    assets = PortfolioAssetInSerializer(many=True, required=False)

    def validate(self, data):
        assets = data.get("assets") or []
        bw = q2f(data["weight_pct"])
        if assets:
            s = q2f(sum(a["weight_pct"] for a in assets))
            if abs(s - bw) > 0.01:
                raise serializers.ValidationError(
                    f"assets 합({s:.2f}) != 버킷 비중({bw:.2f})"
                )
        for a in assets:
            code = a["code"]
            qs = Asset.objects.filter(code=code, is_enabled=True)
            if not qs.exists():
                raise serializers.ValidationError(f"자산 코드 미존재/비활성: {code}")
            asset = qs.first()
            if asset.asset_type != data["bucket"]:
                raise serializers.ValidationError(
                    f"코드 {code} 의 버킷({asset.asset_type}) != 요청 버킷({data['bucket']})"
                )
        return data


class PortfolioCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=120, required=False, allow_blank=True, default="")
    amount_krw = serializers.IntegerField(min_value=0)
    profile = serializers.CharField(max_length=32)
    profile_label = serializers.CharField(max_length=64)
    horizon_desc = serializers.CharField(max_length=64)

    must_buckets = serializers.ListField(
        child=serializers.ChoiceField(choices=AssetType.choices),
        allow_empty=True,
        required=False,
        default=list,
    )

    rationale = serializers.CharField(required=False, allow_blank=True, default="")
    summary = serializers.CharField(required=False, allow_blank=True, default="")

    allocations = PortfolioAllocationInSerializer(many=True)

    metrics = serializers.JSONField(required=False)

    set_representative = serializers.BooleanField(required=False, default=False)

    def validate_allocations(self, value: List[dict]):
        total = q2f(sum(row.get("weight_pct", 0) for row in value))
        if abs(total - 100.00) > 0.01:
            raise serializers.ValidationError(f"버킷 합계가 100.00이 아닙니다: {total:.2f}")
        buckets = [row["bucket"] for row in value]
        if len(buckets) != len(set(buckets)):
            raise serializers.ValidationError("동일 버킷이 중복되었습니다.")
        return value

    @staticmethod
    def _normalize_allocations_for_storage(allocs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for row in allocs:
            item = {
                "bucket": row["bucket"],
                "weight_pct": q2f(row["weight_pct"]),
                "assets": [
                    {"code": a["code"], "weight_pct": q2f(a["weight_pct"])}
                    for a in (row.get("assets") or [])
                ],
            }
            out.append(item)
        return out

    @transaction.atomic
    def create(self, validated_data):
        user = self.context["request"].user
        allocations = validated_data.pop("allocations")
        set_rep = validated_data.pop("set_representative", False)
        input_metrics = validated_data.pop("metrics", None)

        norm_allocs = self._normalize_allocations_for_storage(allocations)

        if input_metrics:
            metrics_dict = input_metrics
        else:
            metrics_dict = {"expected_return_pct": None, "risk_score": None}
            if compute_portfolio_metrics:
                try:
                    m = compute_portfolio_metrics(norm_allocs)
                    # compute_portfolio_metrics 결과에 risk_score가 직접 없으면 별도 함수 호출
                    rs = m.get("risk_score")
                    if rs is None and risk_score_0_100:
                        rs = risk_score_0_100(m)

                    metrics_dict = {
                        "expected_return_pct": q2f(m.get("expected_return_pct")),
                        "risk_score": q2f(rs),
                    }
                except Exception:
                    pass

        portfolio = Portfolio.objects.create(
            user=user,
            allocations=norm_allocs,
            metrics=metrics_dict,
            **validated_data,
        )

        if set_rep:
            portfolio.set_representative()

        return portfolio


# ------- 출력 --------

class PortfolioDetailSerializer(serializers.ModelSerializer):
    # 모델에 없는 필드 참조 제거: ai_proposed_allocations ❌
    # corrections 필드가 모델에 없더라도 안전하게 처리하고 싶다면 아래처럼 주석 해제:
    # corrections = serializers.SerializerMethodField()
    #
    # def get_corrections(self, obj):
    #     return getattr(obj, "corrections", []) or []

    class Meta:
        model = Portfolio
        fields = (
            "id", "name",
            "amount_krw", "profile", "profile_label", "horizon_desc",
            "must_buckets", "corrections",
            "rationale", "summary",
            "is_representative",
            "generated_at", "created_at", "updated_at",
            "allocations", "metrics",
        )


class PortfolioListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Portfolio
        fields = (
            "id", "name", "is_representative", "created_at",
            "amount_krw", "profile", "profile_label", "horizon_desc",
            "metrics",
        )