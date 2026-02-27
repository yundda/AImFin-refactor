# scripts/ai_benchmark.py
import os
import sys
import django
import time
import json
import statistics
import re
import logging

# Django 환경 설정
sys.path.append(os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aim_fin.settings.base")
django.setup()

from django.conf import settings
from users.models import User, SurveyResult, UserRiskSnapshot, RiskProfileCode, InvestmentPreference
from analysis.services.recommend import recommend_portfolio, recommend_portfolio_v1_single

# 로깅 비활성화 (벤치마크 출력 집중)
logging.disable(logging.WARNING)

def setup_test_user(email):
    """
    벤치마크에 필요한 최소 정보를 가진 테스트 유저 생성/업데이트.
    """
    user, created = User.objects.get_or_create(email=email, defaults={"nickname": "BenchmarkTester"})
    if created:
        user.set_password("benchmark123!")
        user.save()
    
    # 리스크 설문 결과 생성
    survey, _ = SurveyResult.objects.get_or_create(
        user=user,
        defaults={
            "total_score": 75,
            "profile": RiskProfileCode.GROWTH,
            "section_scores": {"attitude": 80, "experience": 70},
            "survey_json": {"q1": "a1"}
        }
    )
    
    # 리스크 스냅샷 생성
    UserRiskSnapshot.objects.update_or_create(
        user=user,
        defaults={"latest_result": survey}
    )
    
    # 투자 선호도 생성
    InvestmentPreference.objects.update_or_create(
        user=user,
        defaults={
            "amount_krw": 10000000,
            "horizon_code": "Y_3_5",
            "include_products": ["DOMESTIC_STOCK", "GLOBAL_STOCK"]
        }
    )
    return user

def calculate_delta(proposed, final):
    """
    AI 제안(proposed)과 서버 보정(final) 간의 비중 편차 합산.
    """
    p_map = {a['bucket']: float(a['weight_pct']) for a in proposed}
    f_map = {a['bucket']: float(a['weight_pct']) for a in final}
    
    deltas = []
    all_buckets = set(p_map.keys()) | set(f_map.keys())
    for b in all_buckets:
        p = p_map.get(b, 0.0)
        f = f_map.get(b, 0.0)
        deltas.append(abs(p - f))
    
    return sum(deltas), max(deltas) if deltas else 0

def check_consistency(rationale, final):
    """
    해설(rationale) 텍스트 내의 숫자%와 최종 데이터 간의 정합성 체크.
    """
    f_weights = {float(a['weight_pct']) for a in final}
    matches = re.findall(r"(\d+(?:\.\d+)?)\s*%", rationale)
    
    if not matches:
        return True # 문구에 숫자가 없으면 정합성 오류로 보지 않음
    
    mismatch_count = 0
    for m in matches:
        val = float(m)
        # 소수점 오차 감안
        found = any(abs(val - fw) < 0.1 for fw in f_weights)
        if not found:
            mismatch_count += 1
            
    return mismatch_count == 0

def print_summary(results, name):
    latencies = [r['latency'] for r in results]
    tokens = [r['tokens'] for r in results]
    deltas = [r['delta_abs'] for r in results]
    mismatches = [1 if not r['consistent'] else 0 for r in results]
    violations = [r['violations'] for r in results]
    
    avg_latency = statistics.mean(latencies)
    p95_latency = statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies)
    avg_tokens = statistics.mean(tokens)
    avg_delta = statistics.mean(deltas)
    mismatch_rate = (sum(mismatches) / len(results)) * 100
    avg_violations = statistics.mean(violations)

    print(f"\n=== [Benchmark Result: {name}] ===")
    print(f"Trials: {len(results)}")
    print(f"Avg Latency: {avg_latency:.2f}ms")
    print(f"P95 Latency: {p95_latency:.2f}ms")
    print(f"Avg Tokens:  {avg_tokens:.2f}")
    print(f"Avg Correction Delta: {avg_delta:.2f}%")
    print(f"Avg Policy Violations: {avg_violations:.2f} items")
    print(f"Consistency Mismatch Rate: {mismatch_rate:.2f}%")

def run_benchmark(email, trials=10):
    # 시뮬레이션 모드 활성화
    settings.AI_MOCK_MODE = True
    user = setup_test_user(email)
    
    results_a = []
    results_b = []
    
    print(f"Starting AI Reliability Benchmark (User: {email}, Trials: {trials})")
    print("-" * 60)

    for i in range(trials):
        print(f"[{i+1}/{trials}] Testing...", end="\r")
        
        # Test Ver A (Single Pass)
        try:
            res_a = recommend_portfolio_v1_single(
                user=user, 
                amount_krw=10000000, 
                horizon_desc="3~5년", 
                must_buckets=["STOCKS_KR", "STOCKS_GLB"],
                benchmark_mode=True
            )
            d_abs, _ = calculate_delta(res_a['proposed_allocations'], res_a['final_allocations'])
            consistent = check_consistency(res_a['rationale'], res_a['final_allocations'])
            metrics_a = res_a['_metrics_logs'][0]
            results_a.append({
                "latency": metrics_a['latency_ms'],
                "tokens": metrics_a['total_tokens'],
                "delta_abs": d_abs,
                "consistent": consistent,
                "violations": len(res_a['corrections'])
            })
        except Exception as e:
            print(f"\nError in Ver A Trial {i+1}: {e}")

        # Test Ver B (Double Pass)
        try:
            res_b = recommend_portfolio(
                user=user, 
                amount_krw=10000000, 
                horizon_desc="3~5년", 
                must_buckets=["STOCKS_KR", "STOCKS_GLB"],
                benchmark_mode=True
            )
            d_abs, _ = calculate_delta(res_b['proposed_allocations'], res_b['final_allocations'])
            consistent = check_consistency(res_b['rationale'], res_b['final_allocations'])
            m_logs = res_b['_metrics_logs']
            results_b.append({
                "latency": sum(m['latency_ms'] for m in m_logs),
                "tokens": sum(m['total_tokens'] for m in m_logs),
                "delta_abs": d_abs,
                "consistent": consistent,
                "violations": len(res_b['corrections'])
            })
        except Exception as e:
            print(f"\nError in Ver B Trial {i+1}: {e}")

    print("\nBenchmark completed.")
    print_summary(results_a, "Ver A: Single-Pass (Naive)")
    print_summary(results_b, "Ver B: Double-Pass (Reliable)")
    
    # 보고서용 JSON 저장
    with open("ai_benchmark_summary.json", "w", encoding="utf-8") as f:
        json.dump({"Ver_A": results_a, "Ver_B": results_b}, f, indent=2, ensure_ascii=False)
    print("\nDetailed results saved to 'ai_benchmark_summary.json'.")

if __name__ == "__main__":
    # 기본 유저로 실행
    target_email = "vvvzzang1218@gmail.com"
    run_benchmark(target_email, trials=10) # 시간 관계상 10회로 우선 테스트
