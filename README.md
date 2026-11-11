# Gayatri AI — Enterprise Educational Intelligence Platform

**Gayatri AI** is a full-stack enterprise educational intelligence platform built for AI and Machine Learning cohorts. It unifies longitudinal student telemetry, cross-validated academic risk forecasting, unsupervised learner persona clustering, prerequisite-aware knowledge tracing, hybrid curriculum recommendations, automated psychometric assessment evaluation, a curriculum-grounded academic assistant, and exportable PDF/CSV reports inside a responsive dark-theme React and FastAPI workspace.

---

## Key Capabilities

### Learner Intelligence Workspace (Student Role)
- **Intelligence Hub**: Projected final score forecast, cumulative GPA, concept mastery average, study engagement and attendance index, predictive risk probability, K-Means behavioral persona assignment, 10-week score trajectory with 4-week damped Ridge confidence intervals, and local z-score feature attribution drivers.
- **Courses & Adaptive Recommendations**: 6 structured AI/ML courses spanning 24 prerequisite-linked concepts and 24 learning modules ranked dynamically via `TfidfVectorizer` cosine similarity, mastery-gap urgency, prerequisite readiness gating, and difficulty alignment.
- **Interactive Assessment Center**: Timed domain evaluations with instant server-side grading (correct answers stripped from pre-submission GET responses), concept mastery propagation, real-time ML risk recalculation, and post-submission answer review.
- **Longitudinal Analytics & Telemetry Check-In**: Personal weekly score, study hours, attendance trajectory vs cohort averages, interactive study check-in logging, and prerequisite mastery matrix.
- **Academic Intelligence Assistant**: Persistent conversational tutor grounded in live student concept mastery, assessment history, and TF-IDF curriculum retrieval with clickable module citations and quick actions.
- **Export Reports**: One-click personal PDF academic progress transcripts (ReportLab + Matplotlib charts) and CSV telemetry exports.

### Enterprise Governance Console (Administrator Role)
- **Command Center**: Institutional cohort KPIs across 100 seeded learners, 10-week institutional engagement trends, 2D PCA learner segmentation scatter map, and course bottleneck diagnostics.
- **Student Directory & Interventions**: Searchable and filterable cohort roster with risk stratification badges, individual learner drill-downs, advisor outreach logging (`Pending`, `In Progress`, `Resolved`), and immutable security audit trail inspection.
- **Assessment Studio & Psychometrics**: Custom assessment creation across curriculum concepts plus Kelley upper-lower 27% Item Discrimination Index ($D$) and Item Difficulty ($p$-value) calibration per question.
- **ML Pipeline & Evaluation Console**: Live 5-fold Stratified Cross-Validation classifier comparison (`RandomForestClassifier`, `GradientBoostingClassifier`, `LogisticRegression`), regression benchmarks (`RidgeRegressor`, `GradientBoostingRegressor`), out-of-fold confusion matrix, global Gini feature importances, K-Means + PCA cluster diagnostics, and live model retraining trigger.

---

## Architecture & Tech Stack

Gayatri AI is structured as a decoupled four-tier application:

1. **Presentation Tier (`frontend/`)**: React 18.3, TypeScript 5.6, Vite 5.4, Tailwind CSS 3.4, Recharts 2.13, and Lucide React. Enforces role-aware routing (`student` vs `admin`), persists JWT bearer tokens, renders interactive telemetry and PCA charts, and adapts cleanly across desktop (`1440px`), tablet (`768px`), and mobile (`390px`) viewports.
2. **API & Security Gateway (`backend/app/api/`, `backend/app/core/`)**: FastAPI 0.116 ASGI application exposing 32 versioned REST endpoints under `/api/v1` (plus `/health`, `/docs`, `/redoc`). Uses Pydantic v2 strict validation, salted `bcrypt` (`rounds=12`) password hashing, HS256 JWT bearer auth, `require_role` guards, request timing middleware (`X-Process-Time-Ms`), and immutable audit logging.
3. **AI/ML & Domain Engine (`backend/app/ml/`, `backend/app/services/`)**: Scikit-Learn 1.9, NumPy 2.3, Pandas 2.3, SciPy 1.18, Joblib, ReportLab 4.4, and Matplotlib 3.10 powering leakage-free cross-validated risk pipelines, local feature drivers, K-Means + PCA clustering, EWMA mastery tracing, hybrid TF-IDF recommendations, RAG tutoring, Kelley 27% item psychometrics, and binary PDF/CSV streaming exports.
4. **Persistence Layer (`backend/app/db/`)**: SQLAlchemy 2.0.46 over 16 normalized relational tables (`users`, `student_profiles`, `audit_logs`, `courses`, `concepts`, `enrollments`, `concept_masteries`, `learning_resources`, `resource_interactions`, `assessments`, `assessment_questions`, `assessment_submissions`, `question_responses`, `weekly_telemetry`, `interventions`, `assistant_messages`) with foreign-key enforcement (`PRAGMA foreign_keys=ON` in SQLite), `selectinload` query optimization, and full PostgreSQL compatibility via `DATABASE_URL`.

---

## Measured AI/ML Evaluation Summary

Evaluated via 5-fold Stratified Cross-Validation inside `StandardScaler` pipelines on the seeded 100-learner institutional cohort (25 at-risk labels isolated strictly from course grade outcomes `< 68.0` to prevent target leakage):

- **Selected Risk Classifier**: `RandomForestClassifier` — Accuracy `0.9300`, Precision `0.8462`, Recall `0.8800`, F1-Score `0.8627`, ROC-AUC `0.9355`, out-of-fold confusion matrix `[[71, 4], [3, 22]]`
- **Candidate Classifiers**: `LogisticRegression` (Accuracy `0.9100`, F1 `0.8302`, ROC-AUC `0.9600`), `GradientBoostingClassifier` (Accuracy `0.8900`, F1 `0.7660`, ROC-AUC `0.9117`)
- **Selected Score Regressor**: `RidgeRegressor` — MAE `2.4571`, RMSE `3.1078`, $R^2$ `0.9185` (vs `GradientBoostingRegressor` MAE `2.7879`, RMSE `3.3981`, $R^2$ `0.9026`)
- **Unsupervised Segmentation (`KMeans k=4` + `PCA 2D`)**: Silhouette Score `0.2982`, Calinski-Harabasz Index `93.94`, 2D PCA Explained Variance `[0.7472, 0.1130]` (`86.02%` cumulative)

---

## Repository Structure

```text
.
├── .env.example
├── .gitignore
├── README.md
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   ├── pytest.ini
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py
│   │   ├── api/v1/          # auth, students, courses, assessments, assistant, analytics, admin, ml, reports
│   │   ├── core/            # config, logging_config, security
│   │   ├── db/              # base, session, models (16 ORM tables), curriculum_data, seed
│   │   ├── ml/              # feature_engineering, risk_predictor, learner_clustering, knowledge_tracing, recommender, academic_assistant, model_registry
│   │   ├── schemas/         # Pydantic v2 domain schemas
│   │   └── services/        # assessment_engine, report_generator
│   └── tests/               # pytest integration test suite
└── frontend/
    ├── Dockerfile
    ├── index.html
    ├── nginx.conf
    ├── package.json
    ├── package-lock.json
    ├── postcss.config.js
    ├── tailwind.config.js
    ├── tsconfig.json
    ├── tsconfig.node.json
    ├── vite.config.ts
    └── src/
        ├── api/             # Authenticated REST & Blob client
        ├── components/      # BrandLogo, responsive Layout, UI primitives
        ├── context/         # AuthContext (JWT session state)
        ├── pages/           # Student & Admin views (10 pages)
        └── types/           # TypeScript interfaces
```

---

## Dependencies & Setup

### Prerequisites
- Python `3.11+` (verified on `3.13.14`)
- Node.js `18+` and `npm`

### 1. Environment Configuration

Copy `.env.example` to `.env` in the repository root and set a strong `SECRET_KEY` (at least 32 random characters):

```powershell
Copy-Item .env.example .env
```

For local evaluation without `.env`, the backend runs out-of-the-box with local SQLite (`backend/data/gayatri_ai.db`) and development CORS origins. Never commit `.env` files or secrets.

### 2. Install & Run Backend (FastAPI)

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate

pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

On initial startup, the backend initializes the 16 SQLite tables, deterministically seeds the 100-learner institutional cohort (if empty), trains the ML risk, regression, and K-Means pipelines, and persists artifacts to `backend/ml_artifacts/`.

- **Health Check**: `http://127.0.0.1:8000/health`
- **Interactive OpenAPI Docs**: `http://127.0.0.1:8000/docs`

### 3. Install & Run Frontend (React + Vite)

In a separate terminal from the repository root:

```powershell
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

Open `http://127.0.0.1:5173` in your browser.

---

## Seeded Evaluation Accounts

| Role | Name | Email | Password | Profile Focus |
| --- | --- | --- | --- | --- |
| **Student** | Ananya Sharma | `ananya.sharma@gayatri-ai.edu` | `Student@2026` | Consistent Builder cohort learner |
| **Student** | Rohan Verma | `rohan.verma@gayatri-ai.edu` | `Student@2026` | Elevated-risk intervention profile |
| **Admin** | Dr. Kavita Rao | `admin@gayatri-ai.edu` | `Admin@Gayatri2026` | Full institutional command access |

New student accounts can also be registered directly via the login screen (`POST /api/v1/auth/register`).

---

## REST API Reference

All domain endpoints sit under `/api/v1` (with interactive OpenAPI schemas at `/docs` and `/redoc`):

| Group | Method & Path | Access | Description |
| --- | --- | --- | --- |
| **System** | `GET /health` | Public | Database connectivity and service health probe |
| **Auth** | `POST /api/v1/auth/login` | Public | Authenticate credentials and issue HS256 JWT |
| **Auth** | `POST /api/v1/auth/register` | Public | Register and initialize a new student workspace |
| **Auth** | `GET /api/v1/auth/me` | Authenticated | Return active user profile and role |
| **Students** | `GET /api/v1/students/me/dashboard` | Student / Admin | Aggregate student intelligence payload, drivers, forecast, recs |
| **Students** | `GET /api/v1/students/{student_id}/dashboard` | Self / Admin | Drill-down student intelligence dashboard |
| **Students** | `POST /api/v1/students/me/telemetry` | Student | Log weekly study hours, attendance, and confidence check-in |
| **Courses** | `GET /api/v1/courses` | Authenticated | List curriculum courses and learner progress |
| **Courses** | `GET /api/v1/courses/{course_id}` | Authenticated | Course detail with concept prerequisites and learning modules |
| **Courses** | `GET /api/v1/courses/recommendations` | Authenticated | Personalized TF-IDF + mastery-gap ranked modules |
| **Courses** | `POST /api/v1/courses/resources/{resource_id}/interact` | Authenticated | Mark module opened/completed and trigger mastery propagation |
| **Assessments** | `GET /api/v1/assessments` | Authenticated | Available assessments and submission summaries |
| **Assessments** | `GET /api/v1/assessments/{assessment_id}` | Authenticated | Fetch questions (answer keys stripped for learners) |
| **Assessments** | `POST /api/v1/assessments/{assessment_id}/submit` | Authenticated | Grade responses, update mastery, recompute ML risk score |
| **Assessments** | `GET /api/v1/assessments/submissions/{submission_id}` | Self / Admin | Detailed question-by-question review and explanations |
| **Assessments** | `POST /api/v1/assessments` | Admin | Create new curriculum-linked assessment |
| **Assessments** | `GET /api/v1/assessments/concepts/catalog` | Admin | Concept catalog for assessment authoring |
| **Assessments** | `GET /api/v1/assessments/{assessment_id}/psychometrics` | Admin | Item Difficulty ($p$-value) & Kelley 27% Discrimination ($D$) |
| **Assistant** | `POST /api/v1/assistant/query` | Authenticated | Submit RAG tutoring or institutional analytics prompt |
| **Assistant** | `GET /api/v1/assistant/history` | Authenticated | Retrieve persisted dialogue and citations |
| **Assistant** | `DELETE /api/v1/assistant/history` | Authenticated | Clear active user's assistant thread |
| **Analytics** | `GET /api/v1/analytics/student` | Self / Admin | Longitudinal trajectory, cohort comparison, mastery heatmap |
| **Analytics** | `GET /api/v1/analytics/cohort` | Admin | Cohort KPIs, weekly institutional trends, bottlenecks |
| **Admin** | `GET /api/v1/admin/students` | Admin | Searchable, risk-filterable cohort directory |
| **Admin** | `GET /POST /api/v1/admin/interventions` | Admin | List and log structured advisor outreach interventions |
| **Admin** | `PATCH /api/v1/admin/interventions/{intervention_id}` | Admin | Update intervention workflow status (`Pending`/`In Progress`/`Resolved`) |
| **Admin** | `GET /api/v1/admin/audit-logs` | Admin | View recent security & operational audit records |
| **ML Ops** | `GET /api/v1/ml/metrics` | Admin | Retrieve cross-validation benchmarks, confusion matrix, clusters |
| **ML Ops** | `POST /api/v1/ml/retrain` | Admin | Recompute cohort features and retrain ML pipelines live |
| **Reports** | `GET /api/v1/reports/student/{student_id}/pdf` | Self / Admin | Stream downloadable Student PDF Transcript |
| **Reports** | `GET /api/v1/reports/student/{student_id}/csv` | Self / Admin | Stream downloadable Student Telemetry CSV |
| **Reports** | `GET /api/v1/reports/cohort/pdf` | Admin | Stream Executive Cohort Intelligence PDF Report |
| **Reports** | `GET /api/v1/reports/cohort/csv` | Admin | Stream Full Cohort ML & Risk CSV Dataset |

---

## Testing & Verification

```powershell
# Backend integration & ML/RBAC/Report test suite (9 tests)
cd backend
python -m pytest -v

# Frontend strict TypeScript check + Vite production bundle
cd ..\frontend
npm run build
```

Verified locally:
- **Backend Pytest Suite**: `9 passed in 125.04s` (`test_health_check`, `test_authentication_and_rbac_enforcement`, `test_student_dashboard_recommendations_and_checkin`, `test_course_resource_completion_updates_mastery`, `test_assessment_submission_and_psychometrics`, `test_academic_assistant_rag_and_telemetry_grounding`, `test_ml_metrics_retrain_and_interventions`, `test_pdf_and_csv_report_exports`, `test_student_registration_flow`).
- **Frontend Production Build**: `tsc && vite build` compiled `2189` modules cleanly into `dist/`.
- **Docker Compose Configuration**: `docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile`, and `frontend/nginx.conf` are included for containerized hosting (`docker compose up --build -d`; container runtime not executed locally).
