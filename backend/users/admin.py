from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import (
    SurveyResult,
    UserRiskSnapshot,
    InvestmentPreference,
    UserPreferenceSnapshot,
)

User = get_user_model()

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "nickname", "date_joined")
    search_fields = ("email", "nickname")
    ordering = ("-id",)

admin.site.register(SurveyResult)
admin.site.register(UserRiskSnapshot)
admin.site.register(InvestmentPreference)
admin.site.register(UserPreferenceSnapshot)
