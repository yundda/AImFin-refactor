#!/bin/bash

# AImFin 배포 베이스라인 스모크 테스트 스크립트
# 사용법: sh tests/smoke_test.sh

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "🔍 AImFin 배포 베이스라인 스모크 테스트 시작..."

# 1. 컨테이너 상태 확인
echo -n "1. 컨테이너 헬스 체크: "
HEALTHY_COUNT=$(docker ps --format "{{.Status}}" | grep -c "healthy")
TOTAL_COUNT=3 # mysql, redis, backend (nginx는 healthcheck 없음)
if [ "$HEALTHY_COUNT" -ge "$TOTAL_COUNT" ]; then
    echo "${GREEN}PASS${NC} ($HEALTHY_COUNT healthy containers found)"
else
    echo "${RED}FAIL${NC} (Only $HEALTHY_COUNT/$TOTAL_COUNT containers are healthy)"
    # 어떤 컨테이너가 문제인지 출력
    docker ps --format "table {{.Names}}\t{{.Status}}"
fi

# 2. HTTP -> HTTPS 리다이렉트 확인
echo -n "2. HTTP -> HTTPS 리다이렉트 확인: "
REDIRECT_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost)
if [ "$REDIRECT_CODE" = "301" ] || [ "$REDIRECT_CODE" = "308" ]; then
    echo "${GREEN}PASS${NC} (Code: $REDIRECT_CODE)"
else
    echo "${RED}FAIL${NC} (Unexpected code: $REDIRECT_CODE)"
fi

# 3. HTTPS 접속 확인 (Self-signed 인증서이므로 -k 사용)
echo -n "3. HTTPS 및 Nginx 메인(프론트/정적) 접속 확인: "
HTTPS_CODE=$(curl -k -s -o /dev/null -w "%{http_code}" https://localhost)
if [ "$HTTPS_CODE" = "200" ] || [ "$HTTPS_CODE" = "302" ]; then
    echo "${GREEN}PASS${NC} (Code: $HTTPS_CODE)"
else
    echo "${RED}FAIL${NC} (Unexpected code: $HTTPS_CODE)"
fi

# 4. API 프록시 확인 (Django Admin 호출 시도)
echo -n "4. API 프록시 (Django Admin) 연동 확인: "
API_CODE=$(curl -k -s -o /dev/null -w "%{http_code}" https://localhost/admin/login/)
if [ "$API_CODE" = "200" ]; then
    echo "${GREEN}PASS${NC} (Code: $API_CODE)"
else
    echo "${RED}FAIL${NC} (Unexpected code: $API_CODE)"
fi

# 5. 정적 파일 접근 확인 (Swagger Sidecar CSS 등)
echo -n "5. 정적 파일 서빙 확인: "
STATIC_CODE=$(curl -k -s -o /dev/null -w "%{http_code}" https://localhost/static/drf_spectacular_sidecar/swagger-ui.css)
if [ "$STATIC_CODE" = "200" ]; then
    echo "${GREEN}PASS${NC} (Code: $STATIC_CODE)"
else
    # 파일이 없을 수 있으므로 admin/css로 재시도
    STATIC_CODE=$(curl -k -s -o /dev/null -w "%{http_code}" https://localhost/static/admin/css/base.css)
    if [ "$STATIC_CODE" = "200" ]; then
        echo "${GREEN}PASS${NC} (Code: $STATIC_CODE)"
    else
        echo "${RED}FAIL${NC} (Unexpected code: $STATIC_CODE)"
    fi
fi

echo "✅ 스모크 테스트 완료."
