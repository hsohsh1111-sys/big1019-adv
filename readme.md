# 심화_생성형 AI와 AWS 클라우드를 활용한 풀스택 & 자동화 실무 개발

> 생성형 AI · RPA · 코드 품질 · MLOps · 보안/DevOps를 **90시간** 동안 브라우저에서 실행되는 예제로 학습합니다.

## � 시간 배분 (총 90h)

| 파트 | 주제 | 예제 수 | 시간 |
|---|---|:---:|:---:|
| [p01](p01_생성형AI_활용개발) | 생성형 AI 활용 개발 | 5 | 20h |
| [p02](p02_RPA_고급개발_연계자동화) | RPA 고급 개발 및 연계 자동화 | 5 | 18h |
| [p03](p03_실전_코드리뷰_최적화) | 실전 코드 리뷰 및 최적화 | 4 | 14h |
| [p04](p04_MLOps_데이터엔지니어링) | MLOps 및 데이터 엔지니어링 | 6 | 22h |
| [p05](p05_보안_DevOps) | 보안 및 DevOps | 5 | 16h |
| **합계** | | **25** | **90h** |

## 📚 파트별 학습 내용

### p01. 생성형 AI 활용 개발 (20h)

| 예제 | 학습 내용 | 시간 |
|---|---|:---:|
| 01_openai_chatbot | OpenAI API 챗봇, 대화 기록(history)과 토큰 | 3h |
| 02_gemini_chatbot | Gemini API 챗봇, FAQ + AI 자동 응답 시스템 | 4h |
| 03_langchain_agent | LangChain 도구 사용 에이전트, LCEL 파이프라인 | 5h |
| 04_doc_summarizer | 문서 요약·정보 추출, 보고서 자동 생성 | 3h |
| 05_ai_db_webapp | AI + DB 웹앱 (FastAPI + SQLite, 간단한 RAG) | 5h |

### p02. RPA 고급 개발 및 연계 자동화 (18h)

| 예제 | 학습 내용 | 시간 |
|---|---|:---:|
| 01_web_scraping | requests + BeautifulSoup 스크래핑, CSV·엑셀 저장 | 4h |
| 02_ui_automation | Playwright로 엑셀 명단 → 웹 폼 자동 입력 | 4h |
| 03_ai_script_runner | LLM 기반 자동화 스크립트 (계획 → 검증 → 실행) | 3h |
| 04_email_document | 수료증(Word) 생성 + 메일 자동 발송 | 3h |
| 05_rpa_ai_pipeline | 수집(RPA) → 분류(AI) → 사람 검토 → 보고 | 4h |

### p03. 실전 코드 리뷰 및 최적화 (14h)

| 예제 | 학습 내용 | 시간 |
|---|---|:---:|
| 01_refactoring_python | 코드 리뷰·리팩토링, O(n²) → O(n) 성능 개선 | 4h |
| 02_eslint_prettier | ESLint·Prettier 린트와 포맷 | 3h |
| 03_static_analysis | Ruff·SonarQube 정적 분석, 보안 취약점 | 3h |
| 04_github_collab | GitHub Flow, 충돌 해결, 이슈·PR 템플릿, CI | 4h |

### p04. MLOps 및 데이터 엔지니어링 (22h)

| 예제 | 학습 내용 | 시간 |
|---|---|:---:|
| ch01_mlflow_tracking | MLOps 개념, MLflow 실험 추적·모델 레지스트리 | 4h |
| ch02_model_serving | FastAPI 모델 서빙 API, Docker 이미지 | 3h |
| ch03_sagemaker | SageMaker 학습·배포 흐름 (로컬 재현) | 3h |
| ch04_data_pipeline | 날씨 데이터 ETL (수집·정제·검증·적재) | 4h |
| ch05_realtime_analysis | 스트리밍 이상 탐지, 실시간 차트(SSE) | 3h |
| ch06_fastAPI | FastAPI 기초, SQLAlchemy, Pydantic, APIRouter, JWT | 5h |

### p05. 보안 및 DevOps (16h)

| 예제 | 학습 내용 | 시간 |
|---|---|:---:|
| 01_iam_policy_lab | IAM 정책 평가, 보안 그룹 점검 | 3h |
| 02_docker | Dockerfile, Docker Compose (앱 + Redis) | 4h |
| 03_kubernetes | kind 클러스터 배포, 롤링 업데이트·확장 | 4h |
| 04_cicd | GitHub Actions·Jenkins CI/CD 파이프라인 | 3h |
| 05_terraform | Terraform IaC (local · docker · AWS 예시) | 2h |

## ⚙️ 실습 환경

```bash
python -m venv .venv
.venv\Scripts\activate             # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

- 대부분의 예제: 예제 폴더에서 `uvicorn web:app --reload` → http://127.0.0.1:8000
- AI 예제는 `GEMINI_API_KEY`(무료)가 없어도 **모의 모드**로 실행됩니다.
- Docker · Kubernetes · Terraform 예제는 해당 도구 설치가 필요하며, 실제 AWS 실행 시 비용이 발생할 수 있습니다.

## 📁 저장소 구성

```
big1019-adv/
├── readme.md
├── list.md                  # 학습 주제 목록
├── requirements.txt         # 전체 예제 공통 패키지
├── p01_생성형AI_활용개발/
├── p02_RPA_고급개발_연계자동화/
├── p03_실전_코드리뷰_최적화/
├── p04_MLOps_데이터엔지니어링/
└── p05_보안_DevOps/
```
