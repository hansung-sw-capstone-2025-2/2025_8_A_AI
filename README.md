# DiffLens Panel Search AI

https://github.com/user-attachments/assets/8916618c-9827-4a0d-8cb9-5339a6f3f6e3

자연어 기반 패널 검색 및 분석을 위한 AI 핵심 모듈입니다.

## Preview

<img width="4760" height="6736" alt="image" src="https://github.com/user-attachments/assets/7cd8899e-e107-4f6d-83f8-244018cc2da2" />

### Members

<table width="50%" align="center">
    <tr>
        <td align="center"><b>LEAD/BE</b></td>
        <td align="center"><b>FE</b></td>
        <td align="center"><b>FE/DE</b></td>
        <td align="center"><b>BE</b></td>
        <td align="center"><b>AI/DATA</b></td>
    </tr>
    <tr>
        <td align="center"><img src="https://github.com/user-attachments/assets/561672fc-71f6-49d3-b826-da55d6ace0c4" /></td>
        <td align="center"><img src="https://github.com/user-attachments/assets/b95eea07-c69a-4bbf-9a8f-eccda41c410e" /></td>
        <td align="center"><img src="https://github.com/user-attachments/assets/15ac4334-9325-48f1-9cf6-0485f9cf130f"></td>
        <td align="center"><img src="https://github.com/user-attachments/assets/2572fa94-b981-46c6-9731-10c977267e16" /></td>
        <td align="center"><img src="https://github.com/user-attachments/assets/197a24c6-853c-4d63-b026-44032b27a5f1" /></td>
    </tr>
    <tr>
        <td align="center"><b><a href="https://github.com/hardwoong">박세웅</a></b></td>
        <td align="center"><b><a href="https://github.com/nyun-nye">윤예진</a></b></td>
        <td align="center"><b><a href="https://github.com/hyesngy">윤혜성</a></b></td>
        <td align="center"><b><a href="https://github.com/ggamnunq">김준용</a></b></td> 
        <td align="center"><b><a href="https://github.com/hoya04">신정호</a></b></td> 
    </tr>
</table>

## Tech Stack

- **Python 3.11** - 런타임
- **FastAPI** - 웹 프레임워크
- **LangChain 0.3.x** - LLM 프레임워크
- **Anthropic Claude** - LLM (Haiku, Sonnet)
- **Upstage Embedding** - 벡터 임베딩
- **PostgreSQL + pgvector** - 데이터베이스
- **asyncpg** - 비동기 ORM

## Getting Started

### Installation

```bash
# 저장소 클론
git clone https://github.com/hansung-sw-capstone-2025-2/2025_8_A_AI.git
cd 2025_8_A_AI

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt
```

### Environment Variables

```env
# LLM API Keys
ANTHROPIC_API_KEY=sk-ant-api03-xxx
UPSTAGE_API_KEY=up_xxx

# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=panel_search
DB_USER=postgres
DB_PASSWORD=your_password
```

### Run

```bash
python main.py

# 또는
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Project Structure

```
2025_8_A_AI/
├── main.py                  # FastAPI 앱 엔트리포인트
├── src/
│   ├── api/                 # API 라우터 및 스키마
│   │   ├── routes/          # 검색, 추천, 비교 엔드포인트
│   │   └── schemas/         # Request/Response DTO
│   ├── services/            # 비즈니스 로직
│   ├── repositories/        # 데이터 접근 계층
│   ├── llm/                 # LLM 통합 모듈
│   │   ├── client.py        # LLM 클라이언트
│   │   ├── query_parser.py  # 쿼리 파싱
│   │   ├── chart_decider.py # 차트 추천
│   │   ├── embeddings.py    # 임베딩 서비스
│   │   └── profile_generator.py  # 프로필 생성
│   ├── domain/              # 도메인 모델
│   ├── core/                # 설정 및 유틸리티
│   └── utils/               # 상수 정의
├── prompts/                 # LLM 프롬프트 템플릿
│   ├── parse_query.md
│   ├── decide_main_chart.md
│   ├── analyze_cohort_insights.md
│   └── generate_profile.md
└── requirements.txt
```

## Key Features

- **자연어 쿼리 파싱**: 사용자의 자연어 검색어를 구조화된 필터 조건으로 자동 변환
- **하이브리드 검색**: 필터 기반 검색과 벡터 유사도 검색의 조합
- **개인화 추천**: 업종/회원 기반 맞춤형 패널 추천
- **집단 비교 분석**: 두 코호트 간 통계적 차이 분석 및 인사이트 생성
- **지능형 차트 추천**: 데이터 특성에 맞는 최적의 시각화 차트 자동 선택
- **프로필 생성**: 패널 메타데이터 기반 자연어 프로필 자동 생성
- **해시태그 생성**: 마케팅용 해시태그 자동 생성

## API Endpoints

### Search API (`/api/search`)

- `POST /api/search/` - 자연어/필터 기반 패널 검색
- `POST /api/search/search-result/{search_id}/refine` - 검색 결과 필터 추가
- `GET /api/search/search-result/{search_id}/info` - 검색 결과 상세 조회
- `GET /api/search/available-filters` - 사용 가능한 필터 목록

### Recommendations API (`/api/quick-search`)

- `POST /api/quick-search/recommendations` - 업종 기반 패널 추천
- `POST /api/quick-search/recommendations/by-member` - 회원 검색 이력 기반 추천
- `GET /api/quick-search/health` - 추천 서비스 상태 확인

### Comparison API (`/api/cohort-comparison`)

- `POST /api/cohort-comparison/compare` - 두 코호트 비교 분석
- `GET /api/cohort-comparison/metrics` - 비교 가능한 메트릭 목록

## LLM Models

- **claude-3-5-haiku**: 쿼리 파싱, 프로필/해시태그 생성, 빠른 응답
- **claude-sonnet-4-5**: 인사이트 생성, 복잡한 분석
- **embedding-query (Upstage)**: 시맨틱 검색용 벡터 임베딩

## API Documentation

서버 실행 후 아래 URL에서 확인:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## License

이 프로젝트는 한성대학교 기업연계 SW캡스톤디자인 수업에서 진행되었습니다.
