from django.core.cache import cache
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
import FinanceDataReader as fdr
import pandas as pd
from datetime import datetime, timedelta


# 유틸리티 함수 (클래스 밖으로 분리)
def get_krx_listing():
    # 캐시된 맵 조회 (24시간)
    cached_map = cache.get("krx_name_map")
    if cached_map:
        return cached_map
    
    try:
        # KRX 상장 종목 전체 조회 (DataFrame: Code, Name, ...)
        df_krx = fdr.StockListing("KRX")
        # Code를 키, Name을 값으로 하는 딕셔너리 생성
        name_map = dict(zip(df_krx["Code"], df_krx["Name"]))
        
        # 캐싱 (24시간)
        cache.set("krx_name_map", name_map, timeout=60 * 60 * 24)
        return name_map
    except Exception as e:
        print(f"Error fetching KRX listing: {e}")
        return {}


def get_us_listing():
    # 캐시된 리스트 조회 (24시간)
    cached_list = cache.get("us_stock_list")
    if cached_list:
        return cached_list

    try:
        # NASDAQ, NYSE 조회 (S&P500은 403 에러 발생 가능성 있음)
        nasdaq = fdr.StockListing('NASDAQ')
        nyse = fdr.StockListing('NYSE')

        # 필요한 컬럼만 추출하여 리스트로 변환 (Symbol, Name)
        us_stocks = []
        
        for df in [nasdaq, nyse]:
            if 'Symbol' in df.columns and 'Name' in df.columns:
                for _, row in df.iterrows():
                    us_stocks.append({
                        "code": row['Symbol'],
                        "name": row['Name']
                    })
        
        # 중복 제거 (Symbol 기준)
        seen = set()
        unique_stocks = []
        for stock in us_stocks:
            if stock['code'] not in seen:
                seen.add(stock['code'])
                unique_stocks.append(stock)

        # 캐싱 (24시간)
        cache.set("us_stock_list", unique_stocks, timeout=60 * 60 * 24)
        return unique_stocks
    except Exception as e:
        print(f"Error fetching US listing: {e}")
        return []


class MarketIndexView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        # 1. 사용자 선호 또는 기본값 결정
        target_indices = ["USD/KRW", "KS11", "KQ11"]

        # 로그인 사용자라면 DB에서 조회 (캐시 키 분리 필요)
        user_key = "default"
        if request.user.is_authenticated:
            try:
                pref = getattr(request.user, "market_preference", None)
                if pref and pref.indices:
                    target_indices = pref.indices
                    user_key = f"user_{request.user.id}"
            except Exception:
                pass
        
        # 쿼리 파라미터가 있으면 최우선 (테스트 용도 등)
        manual_symbols = request.query_params.get("symbols")
        if manual_symbols:
            target_indices = [s.strip() for s in manual_symbols.split(",") if s.strip()]
            user_key = f"manual_{manual_symbols}"

        # 캐시 키 생성
        target_indices.sort()
        cache_key = f"market_indices_{'_'.join(target_indices)}"
        
        # 캐시 조회
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)

        # 데이터 조회
        results = []
        for symbol in target_indices:
            try:
                # 심볼 매핑 (UI용 이름)
                name = symbol
                is_exchange = False
                
                if symbol == "USD/KRW":
                    name = "원/달러"
                    is_exchange = True
                elif symbol == "KS11":
                    name = "코스피"
                elif symbol == "KQ11":
                    name = "코스닥"
                elif symbol == "US500":
                    name = "S&P 500"
                elif symbol == "IXIC":
                    name = "나스닥"
                elif symbol == "DJI":
                    name = "다우 존스"
                
                # 그 외: 숫자 6자리면 한국 주식일 가능성 높음 -> 이름 매핑 시도
                elif symbol.isdigit() and len(symbol) == 6:
                    krx_map = get_krx_listing()
                    name = krx_map.get(symbol, symbol)
                
                # FDR 호출
                df = fdr.DataReader(symbol, self._get_start_date())
                
                # 데이터 포맷팅 (데이터가 없어도 _format_data에서 처리하여 이름은 반환)
                data = self._format_data(symbol, name, df, is_exchange)
                results.append(data)
            except Exception as e:
                print(f"Error fetching {symbol}: {e}")

        # 캐싱 (10분)
        if results:
            cache.set(cache_key, results, timeout=600)
            
        return Response(results)

    def _get_start_date(self):
        # 약 1달(혹은 20거래일) 전부터 조회 -> 스파크라인용
        return (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

    def _format_data(self, id_str, name, df, is_exchange=False):
        if df.empty:
            return {
                "id": id_str, "name": name, "value": 0,
                "change": 0, "rate": 0, "isUp": False, "chartData": []
            }
        
        # 최신 데이터
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest
        
        value = float(latest["Close"])
        change = value - float(prev["Close"])
        rate = (change / float(prev["Close"])) * 100
        
        # 차트 데이터 (종가 리스트)
        chart_data = df["Close"].ffill().tolist()
        
        # 소수점 처리
        if is_exchange:
            value = round(value, 2)
            change = round(change, 2)
            rate = round(rate, 2)
        else:
            value = round(value, 2)
            change = round(change, 2)
            rate = round(rate, 2)
            
        return {
            "id": id_str,
            "name": name,
            "value": value,
            "change": change,
            "rate": rate,
            "isUp": change > 0,
            "chartData": chart_data
        }


class StockSearchView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        query = request.query_params.get("q", "").strip().upper()  # 대소문자 무시를 위해 대문자 변환
        if not query:
            return Response([])
        
        results = []
        
        # 1. KRX 검색 (이름 포함, 코드 일치)
        krx_map = get_krx_listing()
        for code, name in krx_map.items():
            if query in name or query in code:
                results.append({"name": name, "code": code})
                if len(results) >= 10: 
                    break
        
        # 2. 미국 주식 검색 (Symbol 시작, 이름 포함)
        # KRX 결과가 20개 미만일 때만 검색 수행
        if len(results) < 20:
            us_list = get_us_listing()
            for stock in us_list:
                # Symbol이 query로 시작하거나, Name에 query가 포함될 때
                if stock['code'].upper().startswith(query) or query in stock['name'].upper():
                    results.append(stock)
                    if len(results) >= 20:
                        break
        
        return Response(results)
