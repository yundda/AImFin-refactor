from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from users.models import SurveyResult, RiskProfileCode
from rest_framework import serializers
from .models import (
    SurveyResult,
    InvestmentPreference,
    HorizonCode,
    ProductCode,
)


User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    nickname = serializers.CharField(required=False, allow_blank=True, max_length=30)

    class Meta:
        model = User
        fields = ("id", "email", "password", "nickname")

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

class SurveyResultSerializer(serializers.ModelSerializer):
    profile_label = serializers.CharField(read_only=True)

    class Meta:
        model = SurveyResult
        fields = [
            "id",
            "total_score",
            "profile",
            "profile_label",
            "section_scores",
            "survey_json",
            "created_at",
        ]
        read_only_fields = fields


class InvestmentPreferenceCreateSerializer(serializers.Serializer):
    amount_krw = serializers.DecimalField(max_digits=16, decimal_places=0, min_value=0)
    horizon_code = serializers.ChoiceField(choices=HorizonCode.choices)
    include_products = serializers.ListField(
        child=serializers.ChoiceField(choices=[c.value for c in ProductCode]),
        allow_empty=True,
    )

    def validate_include_products(self, v):
        # 중복 제거 & 길이 제한(선택)
        unique = list(dict.fromkeys(v))
        if len(unique) != len(v):
            return unique
        return v


class InvestmentPreferenceSerializer(serializers.ModelSerializer):
    horizon_label = serializers.SerializerMethodField()

    class Meta:
        model = InvestmentPreference
        fields = (
            "id",
            "amount_krw",
            "horizon_code",
            "horizon_label",
            "include_products",
            "from_survey",
            "created_at",
        )

    def get_horizon_label(self, obj) -> str:
        return obj.get_horizon_code_display()
from .models import UserMarketPreference

class UserMarketPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserMarketPreference
        fields = ("indices", "updated_at")
