# AImFin (Refactoring)

사용자의 투자 성향과 기간을 분석하여 최적의 포트폴리오를 추천하고, 데이터 정합성을 강화한 AI 핀테크 서비스.

---

## 팀 & 역할

| 이름 | 역할 | 주요 담당 |
|:---:|:---:|:---|
| **[윤다선]** | 팀장 / Backend | 도메인·DB 설계, Django REST API, 정책 엔진, 지표 파이프라인 |
| |  | Responses API 연동, 프롬프트 설계, 스키마 검증, 인증/회원, 마이페이지, |
| **[윤강한]** | Frontend / Design | Vue 기반 UI/UX, 화면 설계/데이터 시각화, 상태관리, 차트, 디자인 시스템, 접근성, 인터랙션 |

---

## 프로젝트 목적 및 목표

- **목적**: 포트폴리오 구성 경험이 없는 사용자도 쉽게 접근하고, 경험자는 객관적 비교와 리밸런싱을 통해 빠르게 의사결정하도록 지원합니다.
- **목표**
  1. 추천 초안을 신속히 생성
  2. 정책(제약)을 적용해 현실 가능한 비중만 제공
  3. 일관된 지표 파이프라인으로 숫자와 설명의 불일치 제거
  4. 비교·리밸런싱을 반복 시뮬레이션 가능

---

## 주요 기능

1. **성향 진단**
   - 설문을 통해 성향 라벨 산출(안정형~공격투자형).
   - 성향·기간은 사용자당 최신 스냅샷 1건 유지(항상 최신 맥락 활용).

2. **맞춤 포트폴리오 추천**
   - 사용자가 고른 선호 버킷(필수 포함)을 반영해 배분 초안 생성.
   - 정책 엔진이 min/max·합계=100%·선택 버킷 모드를 보장.
   - 기대수익(%)·위험점수(0–100) 제공.

3. **비교 & 리밸런싱**
   - 저장 전 임시 비중으로 가상 비교, 저장 후 식별자(PK)로 비교 모두 지원.
   - 리밸런싱 결과도 동일 지표 파이프라인으로 재계산.

4. **대시보드**
   - 현재 비중, 기대수익/위험도, 변경 이력 요약.

---

## 시스템 흐름(핵심)

**스키마 고정 → 정책 정규화 → 지표 계산 → 한국어 코멘트 생성**

1. JSON 스키마로 응답 형식 고정(`schemas/*_response.py`).
2. 정책 엔진으로 제약 반영(`portfolio_rules.py`, `policy.py`).
3. 단일 지표 함수로 기대수익·위험도 산출(`compute_portfolio_metrics`).
4. 확정 수치를 근거로 설명 생성(`prompts/*.txt` + `services/*`).

> 발표 팁: “모델 원안(제안) / 최종안(정책 반영) / 보정 로그”를 한 화면에 배치.

---

## 🛠 기술 스택 (Tech Stack)

### Backend
- **Framework**: Django 5, Django REST Framework
- **AI Engine**: Google Gemini 2.0 Flash, OpenAI (Dual-Provider Support)
- **Security**: JWT (HttpOnly Cookie), CSRF Middleware, GMS Proxy
- **Monitoring**: Real-time Analytics Logging (Latency, Tokens, Mismatch Rate)

### Frontend
- **Framework**: Vue 3, Vite
- **UI/UX**: Design System with Data Visualization (Chart.js/D3)

### Infrastructure
- **Container**: Docker, Docker Compose
- **Web Server**: Nginx (Reverse Proxy, TLS/SSL)
- **Database**: MySQL, Redis (Caching)

---

## 정책 엔진(현실 제약 반영)

- **보장 사항**
  - 버킷별 최소/최대 비중 준수
  - 합계 정확히 100%(최대잔여 라운딩)
  - 선택 버킷 모드: 사용자가 선택한 버킷만 사용(엄격) 또는 정책 범위 내 보완 허용(유연)
- **효과**
  - 들쭉날쭉한 초안도 일관된 결과로 수렴
  - 초보자는 단순하게, 숙련자는 옵션으로 정교하게 제어

---

## 📈 AI 벤치마크 결과 (Summary)

30회 반복 테스트(n=30)를 통해 입증된 실측 데이터입니다.

| 구분 | 지연시간 (Avg) | Mismatch Rate | 텍스트-데이터 정합성 |
| :--- | :---: | :---: | :--- |
| **Legacy (v1)** | ~500ms | **12.0%** | AI 환각으로 인한 수치 불일치 발생 |
| **Hardened (v2)** | ~1000ms | **0.0%** | **Double-Pass** 구조로 무결성 100% 확보 |

---

## 📝 실시간 모니터링 로그 예시

실제 서비스 운영 중 터미널에서 확인 가능한 상세 로그 포맷입니다.

```bash
[AI_METRICS] mode:hardened call:proposal provider:gemini latency:488.1ms tokens_total:510
[GUARDRAIL] 서버 가이드라인 적용 (Guardrail Applied) corrections:2 delta_abs_sum:7.5%p
[SUCCESS] 무결성 검증 통과 (Integrity Verified): 최종 분석 데이터 정합성 mismatch_count=0.
```

---

## 빠른 실행 방법 (Docker)

운영 환경과 동일한 설정을 위해 Docker 사용을 권장합니다.

```bash
# 1. 저장소 복제 및 환경 변수 설정
cp env/sample.env env/prod.env

# 2. 서비스 실행
docker compose up -d --build

# 3. 스모크 테스트 (보안/연결 검증)
sh tests/smoke_test.sh
```

