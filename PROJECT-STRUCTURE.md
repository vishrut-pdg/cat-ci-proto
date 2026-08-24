# CAT Cost Intelligence Project Structure

This document describes the repository as it exists now. It is not a proposed future structure.

## 1. Architecture summary

CAT Cost Intelligence is a three-container application:

```text
React browser application
        |
        | HTTP / JSON
        v
FastAPI modular monolith
        |
        | SQLAlchemy Core / Psycopg
        v
PostgreSQL
```

The repository also contains a deterministic opportunity ranker, a grounded Gemini assistant with a local fallback, synthetic database generation, Docker Compose configurations, and Caddy production proxy configuration.

## 2. Repository tree

Generated files such as `__pycache__`, frontend build output, and installed dependencies are omitted.

```text
cat-ci-proto/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   ├── prompts.py
│   │   │   └── tools/opportunity_tools.py
│   │   ├── api/
│   │   │   ├── router.py
│   │   │   └── v1/
│   │   │       ├── assistant.py
│   │   │       ├── auth.py
│   │   │       ├── health.py
│   │   │       ├── investigations.py
│   │   │       ├── opportunities.py
│   │   │       └── recsys.py
│   │   ├── auth/demo_auth.py
│   │   ├── db/session.py
│   │   ├── recsys/
│   │   │   ├── config.py
│   │   │   ├── explanations.py
│   │   │   ├── features.py
│   │   │   ├── filters.py
│   │   │   └── ranker.py
│   │   ├── repositories/
│   │   │   ├── investigation_repository.py
│   │   │   ├── opportunity_repository.py
│   │   │   └── recsys_repository.py
│   │   ├── schemas/
│   │   │   ├── opportunity.py
│   │   │   └── recsys.py
│   │   ├── services/
│   │   │   ├── assistant_service.py
│   │   │   ├── investigation_service.py
│   │   │   ├── opportunity_service.py
│   │   │   └── recsys_service.py
│   │   ├── telemetry/middleware.py
│   │   ├── config.py
│   │   └── main.py
│   ├── Dockerfile
│   ├── README.md
│   ├── main.py
│   ├── pyproject.toml
│   ├── synthetic_data_generator.py
│   └── uv.lock
├── deployment/Caddyfile
├── frontend/
│   ├── public/
│   │   ├── favicon.svg
│   │   └── icons.svg
│   ├── src/
│   │   ├── assets/
│   │   │   ├── hero.png
│   │   │   ├── react.svg
│   │   │   └── vite.svg
│   │   ├── auth/
│   │   │   ├── AuthContext.tsx
│   │   │   └── Routes.tsx
│   │   ├── components/
│   │   │   ├── common/MiniChart.tsx
│   │   │   ├── layout/AppShell.tsx
│   │   │   └── opportunity/SharedOpportunityDetail.tsx
│   │   ├── pages/
│   │   │   ├── finance-analyst/
│   │   │   │   ├── AssigningExpertPage.tsx
│   │   │   │   ├── FinanceAnalystPage.tsx
│   │   │   │   ├── FinanceDashboard.tsx
│   │   │   │   ├── OpportunityDetailPage.tsx
│   │   │   │   ├── OpportunityShortlistingPage.tsx
│   │   │   │   └── PortfolioPages.tsx
│   │   │   ├── investigation-expert/
│   │   │   │   ├── ExpertDashboard.tsx
│   │   │   │   ├── InvestigationDetailPage.tsx
│   │   │   │   └── MyInvestigationsPage.tsx
│   │   │   ├── HomePage.tsx
│   │   │   └── LoginPage.tsx
│   │   ├── services/
│   │   │   ├── api.ts
│   │   │   ├── opportunities.ts
│   │   │   └── recsys.ts
│   │   ├── styles/
│   │   │   ├── global.css
│   │   │   └── refinements.css
│   │   ├── types/
│   │   │   ├── opportunity.ts
│   │   │   └── recsys.ts
│   │   ├── App.css
│   │   ├── App.tsx
│   │   ├── index.css
│   │   └── main.tsx
│   ├── Dockerfile
│   ├── README.md
│   ├── eslint.config.js
│   ├── index.html
│   ├── nginx.conf
│   ├── package.json
│   ├── package-lock.json
│   ├── tsconfig.app.json
│   ├── tsconfig.json
│   ├── tsconfig.node.json
│   └── vite.config.ts
├── postgres/
│   ├── init/001_seed.sql.gz
│   └── Dockerfile
├── AI-LOGIC.md
├── DATA-MODEL.md
├── GCP_DEPLOYMENT.md
├── PLAN.md
├── PRD.md
├── PROJECT-STRUCTURE.md
├── README.md
├── data-seed.sh
├── docker-compose.prod.yaml
└── docker-compose.yaml
```

Python package directories also contain normal `__init__.py` files, omitted above for readability.

## 3. Frontend

### Technology

- React 19
- TypeScript
- Vite 8
- React Router 7
- Nginx in the production frontend container

The frontend is not Astro. Its application entry point is `frontend/src/main.tsx`, and route composition is in `frontend/src/App.tsx`.

### Authentication and routing

`AuthContext.tsx` stores the demo user and token. `Routes.tsx` provides authenticated and role-specific route guards.

Implemented roles:

- `FINANCE_ANALYST`
- `INVESTIGATION_EXPERT`

Implemented browser routes:

```text
/login

/finance-analyst
/finance-analyst/opportunity-shortlisting
/finance-analyst/assigning-an-expert
/finance-analyst/monitor-outcome
/finance-analyst/opportunity-rejection
/finance-analyst/cost-saving
/finance-analyst/monitor-learnings
/finance-analyst/opportunities/:opportunityId

/investigation-expert
/investigation-expert/my-investigations
/investigation-expert/my-investigations/:opportunityId
```

Routes for decision makers, execution owners, and process administrators are not implemented in the current frontend.

### UI organization

- `components/layout/AppShell.tsx` provides the shared authenticated shell.
- `components/opportunity/SharedOpportunityDetail.tsx` provides the common evidence and assistant experience.
- `pages/finance-analyst/` contains opportunity review and portfolio pages.
- `pages/investigation-expert/` contains assigned investigation pages.
- `components/common/MiniChart.tsx` renders small inline charts.

### API access

`services/api.ts` is the shared fetch wrapper. It uses `VITE_API_BASE_URL` when configured, otherwise calls `http://localhost:8000/api/v1`, attaches the demo bearer token, and converts non-success responses into `ApiError`.

`services/opportunities.ts` contains opportunity, ranking-result, and evidence reads. The current `services/recsys.ts` file is an empty placeholder. Pages and `SharedOpportunityDetail.tsx` use the shared `apiGet` and `apiRequest` helpers directly for workflow, status, investigation, and assistant requests.

Financial metrics, rankings, and workflow persistence are handled by the backend rather than calculated in the frontend.

## 4. Backend

### Technology

- Python 3.13 or newer
- FastAPI
- SQLAlchemy Core
- Psycopg 3
- Pydantic and Pydantic Settings
- Google Gen AI dependencies through `google-adk`
- Uvicorn

`backend/app/main.py` creates the FastAPI application. `backend/main.py` is a small compatibility entry point that re-exports the same `app` object.

### Layering

```text
API route
   |
   v
Service
   |
   v
Repository
   |
   v
PostgreSQL
```

| Layer | Current responsibility |
|---|---|
| `api/v1` | HTTP routes, dependencies, request bodies, and error mapping |
| `services` | Business orchestration and response composition |
| `repositories` | SQL reads and writes |
| `schemas` | Pydantic response contracts for opportunities and ranking |
| `recsys` | Eligibility, normalization, weighted ranking, and explanations |
| `agents` | Assistant prompt and grounded opportunity context boundary |
| `auth` | Isolated demo authentication |
| `telemetry` | Request timing and AI interaction telemetry |

Some workflow request models are defined directly in route modules. The table documents the current architectural intent; it does not imply that every route has a separate schema file.

### API groups

All API routes are mounted below `/api/v1`.

#### Health

```text
GET /health
```

#### Demo authentication

```text
POST /auth/login
GET  /auth/me
POST /auth/logout
```

Authentication is deliberately for the demo and is not production SSO.

#### Opportunities

```text
GET  /opportunities
GET  /opportunities/{opportunity_id}
POST /opportunities/{opportunity_id}/status
GET  /opportunities/{opportunity_id}/timeseries
GET  /opportunities/{opportunity_id}/overview
GET  /opportunities/{opportunity_id}/plants
GET  /opportunities/{opportunity_id}/suppliers
GET  /opportunities/{opportunity_id}/logistics
GET  /opportunities/{opportunity_id}/tariff
POST /opportunities/{opportunity_id}/assign
POST /opportunities/{opportunity_id}/withdraw
```

The last two routes are registered by the investigations router.

#### Investigations

```text
GET  /investigations
GET  /investigations/by-opportunity/{opportunity_id}
POST /investigations/{investigation_id}/findings
POST /investigations/{investigation_id}/recommendations
POST /investigations/{investigation_id}/submit
```

#### Recommendation system

```text
POST /recsys/rank
GET  /recsys/recommendations
```

#### AI assistant

```text
POST /assistant/chat
GET  /assistant/sessions/{session_id}
GET  /assistant/history/latest/{opportunity_id}
```

## 5. Recommendation system

The recommendation system is deterministic and explainable. It is not a trained machine-learning model.

```text
Load candidates
      |
      v
Apply eligibility filters
      |
      v
Normalize features
      |
      v
Calculate weighted score
      |
      v
Build explanations
      |
      v
Persist run, results, score components, and reasons
```

Current weights from `backend/app/recsys/config.py`:

| Feature | Weight |
|---|---:|
| Potential savings | 0.25 |
| Cost variance | 0.20 |
| Impact score | 0.15 |
| Logistics variance | 0.15 |
| Tariff variance | 0.10 |
| Data confidence | 0.15 |

See `AI-LOGIC.md` for the detailed calculation and limitations.

## 6. AI assistant

The assistant is scoped to one opportunity. `opportunity_tools.py` loads a structured evidence package containing summary, overview, plant, supplier, logistics, tariff, and time-series data.

```text
Assistant request
      |
      v
Load grounded opportunity evidence
      |
      +--> Vertex AI / Gemini when configured
      |
      +--> deterministic local fallback otherwise
      |
      v
Store session, interaction, and tool-call telemetry
```

The default model is `gemini-2.5-flash`, configurable through `GEMINI_MODEL`. The prompt requires answers to use only supplied evidence and format monetary values in USD.

## 7. PostgreSQL

### Container initialization

`postgres/Dockerfile` copies `postgres/init/001_seed.sql.gz` into `/docker-entrypoint-initdb.d/`. PostgreSQL imports it only when the data directory is initialized for the first time.

The seed is generated by `backend/synthetic_data_generator.py`. `data-seed.sh` is the repository helper for regenerating it.

### Logical schemas and tables

```text
catalog
├── parts
├── part_catalog
├── part_attributes
├── specification_definitions
├── part_specifications
├── equipment_models
└── part_compatibility

supply
├── plants
├── suppliers
└── part_supply

economics
└── part_economic_fact

opportunity
├── opportunities
├── metric_snapshots
├── cost_drivers
├── plant_comparisons
├── supplier_comparisons
├── logistics_components
├── logistics_trend
├── plant_cost_trend
├── supplier_cost_trend
├── tariff_trend
├── tariff_details
├── tariff_comparisons
└── opportunity_events

identity_data
├── roles
├── users
├── user_roles
└── expert_profiles

recsys
├── ranking_runs
├── ranking_results
├── ranking_score_components
└── recommendation_explanations

workflow
├── investigations
├── findings
├── expert_consultations
├── recommendations
├── decisions
├── executions
└── outcomes

telemetry
├── ai_sessions
├── ai_interactions
├── agent_tool_calls
└── api_requests
```

The detailed relational and ML-oriented model is documented in `DATA-MODEL.md`.

## 8. Runtime and deployment

### Local Docker Compose

`docker-compose.yaml` starts:

| Service | Runtime | Published port |
|---|---|---:|
| `postgres` | Custom PostgreSQL image and persistent `cat_ci_data` volume | Internal only |
| `backend` | FastAPI/Uvicorn | `8000` |
| `frontend` | Built React application served by Nginx | `5173` |

```text
Browser :5173
    |
    +--> Frontend container

Browser/API client --> Backend :8000 --> PostgreSQL :5432 internally
```

### Production Docker Compose

`docker-compose.prod.yaml` starts PostgreSQL, the internal backend, the internal frontend, and Caddy on ports 80 and 443.

```text
Caddy :80/:443
    |
    v
Frontend Nginx :80
    |
    +--> Backend :8000 internally
              |
              v
        PostgreSQL :5432 internally
```

The current `deployment/Caddyfile` serves `cat-proto.duckdns.org`, enables compression, adds security headers, and proxies browser traffic to the frontend container. Frontend Nginx serves the single-page application and proxies API traffic in the containerized deployment.

## 9. Configuration

### Backend application settings

Defined in `backend/app/config.py`:

```text
APP_NAME
APP_ENV
DATABASE_URL                 required
API_V1_PREFIX                default: /api/v1
DEMO_AUTH_SECRET
```

### Gemini and Vertex AI settings

```text
GOOGLE_CLOUD_PROJECT
GOOGLE_CLOUD_LOCATION
GOOGLE_GENAI_USE_VERTEXAI
GOOGLE_APPLICATION_CREDENTIALS
GOOGLE_APPLICATION_CREDENTIALS_HOST
GEMINI_MODEL
```

### Frontend setting

```text
VITE_API_BASE_URL
```

When absent during direct local Vite development, the frontend uses `http://localhost:8000/api/v1`. The frontend Dockerfile sets the build-time default to `/api/v1`, which Nginx proxies to the backend container.

## 10. Current scope

Implemented:

- demo login and role guards;
- Finance Analyst opportunity review pages;
- Investigation Expert assignment and investigation pages;
- overview, plant, supplier, logistics, tariff, and trend evidence;
- opportunity status changes and immutable events;
- explainable deterministic ranking;
- grounded assistant sessions and history;
- local and production container definitions;
- deterministic synthetic PostgreSQL seed.

Represented in the database but not exposed as complete frontend workflows:

- decision-maker workflow;
- execution-owner workflow;
- process-administration workflow;
- outcome feedback and model learning.

Not currently present:

- a test directory or automated test suite;
- Redis;
- separate microservices;
- a trained ML ranking model;
- production SSO.

## 11. Reference data

The deterministic seed preserves `OPP-000001` as a stable demonstration record:

```text
Opportunity: OPP-000001
Part:        20R-2009
Component:   HP-100045
Plant:       PIR / Brazil
Unit cost:   USD 421.32
Peer cost:   USD 366.23
Variance:    15%
Savings:     USD 720,000
```

This record is useful for manual API and UI verification. It should not be treated as a special production business rule.

## 12. Documentation map

| File | Purpose |
|---|---|
| `README.md` | Setup, Gemini configuration, development, and architecture summary |
| `PRD.md` | Product requirements and workflow intent |
| `PLAN.md` | Delivery and implementation planning |
| `AI-LOGIC.md` | Ranking and grounded-assistant logic |
| `DATA-MODEL.md` | Relational model and ML-ready data design |
| `GCP_DEPLOYMENT.md` | Google Cloud deployment guidance |
| `PROJECT-STRUCTURE.md` | Current repository and runtime structure |

## 13. Architecture rules

1. A part is master data; an opportunity is a detected business condition involving a part and plant.
2. PostgreSQL is the source of opportunity evidence and workflow state.
3. Ranking calculations and financial metrics belong in the backend.
4. Repositories own SQL; services orchestrate business behavior; API modules expose HTTP routes.
5. Assistant answers must be grounded in the selected opportunity's evidence.
6. Historical snapshots and ranking versions should remain reproducible.
7. The prototype remains a modular monolith until a concrete scaling or ownership need justifies another service.
