from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,  # POST {email, password} → {access, refresh}
    TokenRefreshView,     # POST {refresh} → {access}
    TokenVerifyView,      # POST {token} → 200/401
)
from . import views, views_google, views_kakao, views_survey, views_preference


urlpatterns = [
    path("auth/signup", views.signup, name="register"),
    path("auth/login", views.CustomLoginView.as_view(), name="login"),
    path("auth/refresh", TokenRefreshView.as_view(), name="refresh"),
    path("auth/verify", TokenVerifyView.as_view(), name="verify"),
    path("auth/logout", views.LogoutView.as_view(), name="logout"),

    # 구글 OAuth (서버 주도 + PKCE)
    path("auth/google/start", views_google.GoogleStartView.as_view(), name="google-start"),
    path("auth/google/callback", views_google.GoogleCallbackView.as_view(), name="google-callback"),
    # path("auth/refresh-cookie", views.CookieRefreshView.as_view(), name="refresh-cookie"),

    # 카카오
    path("auth/kakao/start", views_kakao.KakaoStartView.as_view(), name="kakao-start"),
    path("auth/kakao/callback", views_kakao.KakaoCallbackView.as_view(), name="kakao-callback"),

    # 프로필/닉네임
    path("profile", views.ProfileView.as_view(), name="profile"),
    path("profile/nickname", views.NicknameView.as_view(), name="profile-nickname"),

    # 설문/성향
    path("survey/save",   views_survey.survey_save, name="survey-save"),
    path("survey/current",  views_survey.survey_current, name="survey-current"),
     path("survey/status", views_survey.survey_status, name="users.preference.status"),

    # --- [추가] 선호설문 ---
    path("preference/save",    views_preference.preference_save, name="preference-save"),
    path("preference/current", views_preference.preference_current, name="preference-current"),
    path("preference/market",  views_preference.market_preference_get, name="market-preference-get"),
    path("preference/market/save", views_preference.market_preference_update, name="market-preference-save"),
]
