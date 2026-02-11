# portfolios/models.py
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from django.conf import settings
from django.db import models, transaction
from django.db.models import Q
from django.utils import timezone

from users.models import RiskProfileCode  # TextChoices 가정
from assets.enums import AssetType        # TextChoices 가정


def q2(x: Decimal | float | int) -> Decimal:
    """소수 둘째 자리 반올림(은행식 아님)"""
    if not isinstance(x, Decimal):
        x = Decimal(str(x))
    return x.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class Portfolio(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="portfolios",
    )

    name = models.CharField(max_length=120, blank=True, default="")

    # 요약 메타
    amount_krw = models.BigIntegerField()
    profile = models.CharField(max_length=32, choices=RiskProfileCode.choices)
    profile_label = models.CharField(max_length=64)
    horizon_desc = models.CharField(max_length=64)

    # 프론트 입력/정책 정보
    must_buckets = models.JSONField(default=list)          # ["STOCKS_KR", ...]
    corrections = models.JSONField(default=list, blank=True)  # 정책 조정 로그(문자열 리스트)

    # 최종 배분/지표 (저장·조회에 사용)
    allocations = models.JSONField(default=list)           # [{bucket, weight_pct, assets:[{code, weight_pct}]}...]
    metrics = models.JSONField(default=dict)               # {"expected_return_pct": float, "risk_score": float}

    # 서술(라쇼날/요약/리스크)
    rationale = models.TextField(blank=True, default="")
    summary = models.TextField(blank=True, default="")

    # ✅ 대표 포트폴리오 플래그(이름 확정)
    is_representative = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    generated_at = models.DateTimeField(default=timezone.now)  # 추천 생성 기준시각

    class Meta:
        ordering = ["-created_at"]
        # 유저당 대표 1개만 허용 (대표일 때만 유니크)
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=Q(is_representative=True),
                name="unique_representative_per_user",
            )
        ]

    def __str__(self) -> str:
        title = self.name or f"{self.profile_label}·{self.horizon_desc}"
        return f"[{self.user_id}] {title}"

    @transaction.atomic
    def set_representative(self) -> None:
        """이 유저의 다른 대표를 해제하고 자신을 대표로"""
        Portfolio.objects.select_for_update().filter(
            user=self.user, is_representative=True
        ).exclude(pk=self.pk).update(is_representative=False)
        if not self.is_representative:
            self.is_representative = True
            self.save(update_fields=["is_representative"])

