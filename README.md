# AImFin

사용자의 성향과 기간에 맞춰 포트폴리오를 추천하고, 비교·리밸런싱까지 지원하는 핀테크 서비스.

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

## 기술 스택

- **Frontend**: Vue, Vite, Axios, 차트 라이브러리  
- **Backend**: Django 5, DRF, drf-spectacular(OpenAPI, `/api/docs`)  
- **Auth**: JWT(SimpleJWT, 헤더/쿠키)  
- **DB**: SQLite(개발용)  
- **모델 연동**: OpenAI Responses API(구조화 출력), 프록시 게이트웨이  
- **기타**: CORS/CSP, 캐시(LocMem)

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

## 지표 일관 파이프라인

- `compute_portfolio_metrics` 한 곳에서 기대수익(%)과 위험점수(0–100) 산출
- 추천/리밸런싱/비교에서 동일 함수 사용 → “같은 입력 = 같은 숫자”
- 비교 프롬프트에도 외부 계산값을 주입해 숫자·서술 불일치 제거

---

## 비교·리밸런싱 UX

- **비교 API 입력 유연성**
  - 좌/우 모두 `id` 또는 `allocations`(JSON) 입력 가능
  - 저장 전 가상 비교와 저장 후 식별자 비교를 하나의 흐름으로 제공
- **리밸런싱**
  - 프론트에서 보낸 비중을 그대로 분석
  - 정책 위반만 최소 보정하고, 보정 사유를 함께 제공

---

## API 문서

- **OpenAPI(Swagger)**: `/api/docs/`
- **주요 엔드포인트**
  - `POST /api/analysis/recommend/portfolio`
  - `POST /api/analysis/rebalance/portfolio`
  - `POST /api/analysis/compare/portfolio`
  - `GET  /api/portfolios/:id`

> 실제 스펙은 Swagger에서 확인하세요.

---

## 샘플 요청/응답(요약)

### 추천 요청

```json
{
  "amount_krw": 20000000,
  "horizon_desc": "1~3년 (중단기)",
  "must_buckets": ["STOCKS_KR", "STOCKS_GLB"],
  "allow_ai_additions": false
}
```

### 추천 응답

```json
{
  "final_allocations": [
    {"bucket": "STOCKS_KR", "weight_pct": 30, "assets": []},
    {"bucket": "STOCKS_GLB", "weight_pct": 35, "assets": []},
    {"bucket": "BONDS_KR",  "weight_pct": 10, "assets": []},
    {"bucket": "BONDS_GLB", "weight_pct": 7,  "assets": []},
    {"bucket": "ALTERNATIVES", "weight_pct": 8, "assets": []},
    {"bucket": "FUNDS", "weight_pct": 5, "assets": []},
    {"bucket": "CASH",  "weight_pct": 5,  "assets": []}
  ],
  "metrics": {"expected_return_pct": 6.93, "risk_score": 53.20},
  "rationale": "...",
  "summary": "...",
  "corrections": ["normalized to 100.00"],
  "generated_at": "2025-12-24T..."
}
```

---

## 빠른 실행(개발)

```bash
# Backend
python -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 8000

# Frontend
cd frontend
npm install
npm run dev
```

### 환경 변수(.env 예시)

- `AI_API_BASE`, `AI_API_KEY`
- `OPENAI_MODEL`, `AI_API_STYLE=responses`
- `BASE_URL`, `FRONTEND_URL`

---

## 확장 아이디어(요약)

- B2B 연금 포트폴리오: 기관/정책 템플릿을 정책 엔진에 주입
- 감사 로그/설명가능성: “왜 이 비중인가”를 규칙·숫자 기준으로 재현
- 스트레스 테스트: 금리·환율·섹터 충격 시나리오 민감도
- 자동 리밸런싱: 허용 편차·주기 기반 제안/알림

---