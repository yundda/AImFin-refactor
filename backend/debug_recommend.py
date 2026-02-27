import os
import django
import sys
import json

# Django 환경 설정
sys.path.append(os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aim_fin.settings.dev")
django.setup()

from django.contrib.auth import get_user_model
from analysis.services.recommend import recommend_portfolio
from users.models import UserRiskSnapshot, SurveyResult

User = get_user_model()

def debug_recommend():
    # 1. 멱등성을 위해 테스트 유저 확보
    email = "test_debug@example.com"
    user, created = User.objects.get_or_create(email=email, defaults={"nickname": "Debugger"})
    
    # 2. 유저의 위험 성향 스냅샷이 있는지 확인 (없으면 생성)
    if not hasattr(user, "risk_snapshot") or not user.risk_snapshot.latest_result:
        # 가상의 설문 결과 생성
        res = SurveyResult.objects.create(
            user=user,
            total_score=75,
            profile="GROWTH"
        )
        RiskSnapshot_obj, _ = UserRiskSnapshot.objects.update_or_create(
            user=user,
            defaults={"latest_result": res}
        )
    
    print(f"User: {user.email}, Profile: {user.risk_snapshot.latest_result.profile}")
    
    try:
        print("\n--- Calling recommend_portfolio ---")
        result = recommend_portfolio(
            user=user,
            amount_krw=10000000,
            horizon_desc="장기 (5년 이상)",
            must_buckets=["STOCKS_KR", "STOCKS_GLB"]
        )
        print("\n--- Success! ---")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print("\n--- Failed! ---")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_recommend()
