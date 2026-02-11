# users/models.py
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from assets.enums import AssetType


class User(AbstractUser):
    """
    커스텀 유저: 이메일을 아이디로 사용, 닉네임은 표시용(선택)
    """
    username = None  # 기본 username 제거
    email = models.EmailField(unique=True)  # 로그인 ID
    nickname = models.CharField(max_length=30, blank=True, default="", db_index=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []  # createsuperuser 추가 필드 X

    def __str__(self):
        return self.nickname or self.email


class RiskProfileCode(models.TextChoices):
    """
    리스크 성향 코드/라벨 (서비스 전역 기준)
    """
    CONSERVATIVE = "CONSERVATIVE", "안정형"
    MODERATE_CONSERVATIVE = "MODERATE_CONSERVATIVE", "안정추구형"
    BALANCED = "BALANCED", "중립형"
    GROWTH = "GROWTH", "적극투자형"
    AGGRESSIVE = "AGGRESSIVE", "공격투자형"


class SurveyResult(models.Model):
    """
    설문 1회 응답 + 계산 결과(점수, 프로필)를 '이력'으로 저장.
      - survey_json: 설문 원문(payload 전체)
      - breakdown_json: 영역별 점수(경험/여력/목적/태도/기간)
      - total_score: 0~100 스케일 총점
      - profile: 최종 리스크 성향 코드
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="survey_results",
    )

    # 설문 입력 원문 (예: {"products":[...], "history_period":"...", ...})
    survey_json = models.JSONField(default=dict)

    # 계산 결과
    total_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="0.00 ~ 100.00",
    )
    profile = models.CharField(
        max_length=32,
        choices=RiskProfileCode.choices,
        help_text="리스크 성향 코드",
    )

    # 세부 점수(브레이크다운): {"experience_score":..,"capacity_score":..,"goal_score":..,"attitude_score":..,"horizon_score":..}
    section_scores = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "survey_result"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["profile"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=(models.Q(total_score__gte=0) & models.Q(total_score__lte=100)),
                name="survey_result_total_score_0_100",
            ),
        ]

    def __str__(self):
        return f"SurveyResult(user={self.user_id}, profile={self.profile}, score={self.total_score})"

    @property
    def profile_label(self) -> str:
        """라벨 문자열(예: '안정형')"""
        return self.get_profile_display()


class UserRiskSnapshot(models.Model):
    """
    '현재' 투자 성향(최신 설문)을 빠르게 조회하기 위한 스냅샷.
    - 설문 저장 직후 서비스 레이어에서 latest_result를 갱신.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="risk_snapshot",
    )
    latest_result = models.OneToOneField(
        SurveyResult,
        on_delete=models.CASCADE,
        related_name="as_current_for",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_risk_snapshot"

    def __str__(self):
        return f"UserRiskSnapshot(user={self.user_id}, profile={self.latest_result.profile})"
    
class HorizonCode(models.TextChoices):
    LT_1Y = "LT_1Y", "1년 이하"
    Y_1_3 = "Y_1_3", "1~3년"
    Y_3_5 = "Y_3_5", "3~5년"
    GTE_5Y = "GTE_5Y", "5년 이상"


# users/models.py

class ProductCode(models.TextChoices):
    STOCKS_KR     = AssetType.STOCKS_KR,    "국내 주식"
    STOCKS_GLB    = AssetType.STOCKS_GLB,   "해외 주식"
    BONDS_KR      = AssetType.BONDS_KR,     "국내 채권"
    BONDS_GLB     = AssetType.BONDS_GLB,    "해외 채권"
    FUNDS         = AssetType.FUNDS,        "펀드(글로벌 인컴/멀티에셋)"
    ALTERNATIVES  = AssetType.ALTERNATIVES, "대체투자(금·리츠·원자재)"
    CASH          = AssetType.CASH,         "현금성(MMF/예금)"


class InvestmentPreference(models.Model):
    """
    추가 설문(운용금액/기간/선호상품) 1회 저장
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="investment_prefs"
    )
    # 원 단위 금액(정수 저장 권장)
    amount_krw = models.DecimalField(
        max_digits=16, decimal_places=0, validators=[MinValueValidator(0)]
    )
    horizon_code = models.CharField(max_length=16, choices=HorizonCode.choices)
    # 선택한 상품군 코드 리스트(JSON 배열)
    include_products = models.JSONField(default=list)

    # 원본 요청 보관(추후 분석/리플레이)
    raw_payload = models.JSONField(default=dict)

    # 성향 설문과의 연결(있으면 추적용)
    from_survey = models.ForeignKey(
        "users.SurveyResult", null=True, blank=True, on_delete=models.SET_NULL, related_name="preferences"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "investment_preference"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["horizon_code"]),
        ]

    def __str__(self):
        return f"InvestmentPreference(user={self.user_id}, amount={self.amount_krw})"


class UserPreferenceSnapshot(models.Model):
    """
    최신 추가 설문을 O(1)로 조회하기 위한 스냅샷
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="preference_snapshot"
    )
    latest_pref = models.OneToOneField(
        InvestmentPreference, on_delete=models.CASCADE, related_name="as_current_pref_for"
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_preference_snapshot"

    def __str__(self):
        return f"UserPreferenceSnapshot(user={self.user_id}, pref_id={self.latest_pref_id})"
class UserMarketPreference(models.Model):
    """
    유저가 메인 화면 상단 티커에서 보고 싶은 지수/종목 리스트
    indices 예: ["KS11", "KQ11", "USD/KRW", "AAPL", "005930"]
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="market_preference"
    )
    indices = models.JSONField(default=list)  # ["KS11", "KQ11", "USD/KRW"]
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_market_preference"

    def __str__(self):
        return f"{self.user.email} market pref"
