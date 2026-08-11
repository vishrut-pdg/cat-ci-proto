# Project Structure
## CAT Cost Intelligence Platform

**Version:** 0.1  
**Status:** Draft

## 1. Repository

```text
CAT-CI-PROTO/
├── frontend/
├── backend/
├── postgres/
├── synthetic_data_generator.py
├── docker-compose.yaml
├── PRD.md
├── PROJECT-STRUCTURE.md
└── README.md
```

Keep the prototype as a modular monolith until there is a concrete scaling or ownership reason to split services.

## 2. Frontend

Technology:
```text
Astro
```

Recommended structure:

```text
frontend/
├── public/
├── src/
│   ├── components/
│   │   ├── common/
│   │   └── opportunity-detail/
│   │       ├── OpportunityHeader.astro
│   │       ├── OpportunityTabs.astro
│   │       ├── AIAssistantPanel.astro
│   │       ├── AssignExpertCard.astro
│   │       ├── OverviewTab.astro
│   │       ├── PlantsTab.astro
│   │       ├── SuppliersTab.astro
│   │       ├── LogisticsTab.astro
│   │       └── TariffTab.astro
│   │
│   ├── layouts/
│   │   ├── BaseLayout.astro
│   │   ├── OpportunityDetailLayout.astro
│   │   ├── InvestigationExpertLayout.astro
│   │   ├── DecisionMakerLayout.astro
│   │   ├── ExecutionLayout.astro
│   │   └── ProcessAdminLayout.astro
│   │
│   ├── pages/
│   │   ├── index.astro
│   │   ├── finance-analyst/
│   │   │   ├── index.astro
│   │   │   ├── opportunity-shortlisting/
│   │   │   │   ├── index.astro
│   │   │   │   └── hydraulic-pump-brazil/
│   │   │   │       └── index.astro
│   │   │   ├── opportunity-rejection/
│   │   │   ├── cost-saving/
│   │   │   ├── assign-expert/
│   │   │   ├── monitor-outcome/
│   │   │   └── monitor-learnings/
│   │   ├── investigation-expert/
│   │   │   ├── index.astro
│   │   │   └── my-investigations/
│   │   │       └── index.astro
│   │   ├── decision-maker/
│   │   │   └── index.astro
│   │   ├── execution/
│   │   │   └── index.astro
│   │   └── process-admin/
│   │       └── index.astro
│   │
│   ├── services/
│   │   ├── api.ts
│   │   ├── opportunities.ts
│   │   ├── investigations.ts
│   │   └── workflow.ts
│   │
│   ├── types/
│   │   ├── opportunity.ts
│   │   ├── investigation.ts
│   │   └── workflow.ts
│   │
│   ├── data/
│   │   └── roles.ts
│   │
│   └── styles/
│       ├── opportunity-detail.css
│       ├── investigation-expert.css
│       ├── decision-maker.css
│       ├── execution.css
│       └── process-admin.css
│
├── astro.config.mjs
├── package.json
└── tsconfig.json
```

Frontend responsibilities:
- presentation,
- navigation,
- UI state,
- formatting,
- API calls.

Frontend must not:
- calculate ranking,
- calculate potential savings,
- calculate benchmark values,
- construct RecSys explanations,
- enforce workflow transitions,
- contain SQL.

## 3. Frontend API Layer

Use:
```text
src/services/api.ts
src/services/opportunities.ts
src/services/investigations.ts
src/services/workflow.ts
```

Logical opportunity client:
```ts
getOpportunities()
getOpportunity(id)
getOpportunityOverview(id)
getOpportunityPlants(id)
getOpportunitySuppliers(id)
getOpportunityLogistics(id)
getOpportunityTariff(id)
```

## 4. Backend

Technology:
```text
Python
FastAPI
SQLAlchemy Core
Psycopg 3
Pydantic
Pydantic Settings
```

Structure:

```text
backend/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── router.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── health.py
│   │       ├── opportunities.py
│   │       ├── investigations.py
│   │       ├── experts.py
│   │       ├── recommendations.py
│   │       ├── decisions.py
│   │       └── executions.py
│   ├── db/
│   │   ├── __init__.py
│   │   └── session.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── opportunity.py
│   │   ├── investigation.py
│   │   ├── recommendation.py
│   │   ├── decision.py
│   │   └── execution.py
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── opportunity_repository.py
│   │   ├── investigation_repository.py
│   │   ├── expert_repository.py
│   │   └── workflow_repository.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── opportunity_service.py
│   │   ├── investigation_service.py
│   │   ├── assignment_service.py
│   │   ├── decision_service.py
│   │   └── execution_service.py
│   ├── recsys/
│   │   ├── __init__.py
│   │   ├── candidate_generator.py
│   │   ├── filters.py
│   │   ├── features.py
│   │   ├── ranker.py
│   │   ├── explanations.py
│   │   └── config.py
│   └── common/
│       ├── exceptions.py
│       └── constants.py
├── tests/
│   ├── unit/
│   └── integration/
├── .env
├── Dockerfile
├── main.py
├── pyproject.toml
└── uv.lock
```

## 5. Backend Layering

```text
API Router
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

### API
Owns:
- routes,
- path/query params,
- response models,
- HTTP status codes.

Must not contain:
- SQL,
- ranking formulas,
- workflow rules.

### Service
Owns:
- business rules,
- response composition,
- workflow transitions,
- RecSys orchestration.

### Repository
Owns:
- SQL,
- database reads,
- database writes.

### Schemas
Pydantic API contracts.

## 6. Current Opportunity Routes

```text
/api/v1/
├── health
└── opportunities
    ├── GET /
    ├── GET /{opportunity_id}
    ├── GET /{opportunity_id}/overview
    ├── GET /{opportunity_id}/plants
    ├── GET /{opportunity_id}/suppliers
    ├── GET /{opportunity_id}/logistics
    ├── GET /{opportunity_id}/tariff
    ├── POST /{opportunity_id}/shortlist
    ├── POST /{opportunity_id}/reject
    └── POST /{opportunity_id}/assign
```

## 7. RecSys Module

```text
backend/app/recsys/
├── candidate_generator.py
├── filters.py
├── features.py
├── ranker.py
├── explanations.py
└── config.py
```

Responsibilities:

### candidate_generator.py
What entities may become cost-saving opportunities?

### filters.py
Rules:
- active part,
- sufficient history,
- minimum spend,
- valid benchmark,
- not already investigated,
- not in cooldown.

### features.py
Example features:
```text
annual_spend
potential_savings
cost_variance_percent
plant_variance
supplier_variance
logistics_variance
tariff_variance
data_confidence
historical_success
```

### ranker.py
Produces:
```text
base_score
final_score
rank_position
```

### explanations.py
Produces structured reason codes such as:
```text
HIGH_LOGISTICS_COST
HIGH_IMPORT_DUTY
HIGH_UNIT_COST
SAVINGS_OPPORTUNITY
```

## 8. PostgreSQL

```text
postgres/
├── Dockerfile
└── init/
    └── 001_seed.sql.gz
```

Generated by:
```text
synthetic_data_generator.py
```

Development cycle:
```text
synthetic_data_generator.py
         |
         v
001_seed.sql.gz
         |
         v
docker build
         |
         v
PostgreSQL container
```

## 9. PostgreSQL Logical Schemas

```text
PostgreSQL
├── catalog
├── supply
├── economics
├── opportunity
├── identity_data
├── recsys
└── workflow
```

### catalog
```text
parts
part_catalog
part_attributes
specification_definitions
part_specifications
equipment_models
part_compatibility
```

### supply
```text
plants
suppliers
part_supply
```

### economics
```text
part_economic_fact
```

Grain:
```text
Part + Plant + Supplier + Month
```

### opportunity
```text
opportunities
metric_snapshots
cost_drivers
plant_comparisons
supplier_comparisons
logistics_components
logistics_trend
tariff_details
tariff_comparisons
```

### identity_data
```text
users
roles
user_roles
expert_profiles
```

### recsys
```text
ranking_runs
ranking_results
ranking_score_components
recommendation_explanations
```

### workflow
```text
investigations
recommendations
decisions
executions
outcomes
```

## 10. Runtime Data Flow

```text
Astro
  |
  | HTTP / JSON
  v
FastAPI
  |
  v
Service
  |
  v
Repository
  |
  | SQL
  v
PostgreSQL
```

Future ranking flow:
```text
PostgreSQL
    |
Candidate Generator
    |
Hard Filters
    |
Feature Builder
    |
Ranker
    |
Explanation Builder
    |
RecSys Tables
    |
FastAPI
    |
Astro
```

## 11. Reference Integration Record

```text
OPP-000001
├── Part: 20R-2009
├── Component: HP-100045
├── Plant: PIR / Brazil
├── Unit Cost: $421.32
├── Peer Average: $366.23
├── Variance: 15%
└── Potential Savings: $720K
```

Use this as:
- demo data,
- API verification data,
- frontend integration data,
- integration-test fixture.

## 12. Tests

Target:

```text
backend/tests/
├── unit/
│   ├── test_opportunity_service.py
│   ├── test_ranker.py
│   └── test_filters.py
└── integration/
    ├── test_health_api.py
    ├── test_opportunities_api.py
    └── test_opportunity_detail_api.py
```

## 13. Environment Configuration

Local backend `.env`:

```env
APP_NAME=CAT Cost Intelligence API
APP_ENV=development
DATABASE_URL=postgresql+psycopg://cat_ci:cat_ci_dev@localhost:5432/cat_ci
API_V1_PREFIX=/api/v1
```

Later Docker Compose:

```env
DATABASE_URL=postgresql+psycopg://cat_ci:cat_ci_dev@postgres:5432/cat_ci
```

## 14. Final Docker Target

```text
docker-compose.yaml
├── postgres
├── backend
├── frontend
└── redis   # only when needed
```

Runtime:
```text
Browser
   |
Frontend :4321
   |
Backend :8000
   |
   +--> PostgreSQL :5432
   |
   +--> Redis :6379
```

## 15. Development Order

```text
1. Synthetic data generator             DONE
2. PostgreSQL image                     DONE
3. PostgreSQL seed verification         DONE
4. FastAPI foundation                   DONE
5. Opportunity list API                 DONE
6. Opportunity detail APIs              CURRENT
7. RecSys V1
8. Finance Analyst frontend integration
9. Opportunity actions
10. Expert assignment
11. Investigation workflow
12. Decision workflow
13. Execution workflow
14. Outcome feedback
15. Redis / optimization if required
16. Final Docker Compose
17. Deployment hardening
```

## 16. Architecture Rules

1. Part is not Opportunity.
2. Frontend does not calculate financial business metrics.
3. API layer does not contain SQL.
4. Repository layer does not contain UI composition logic.
5. RecSys does not invent source facts.
6. Historical analytical snapshots must remain reproducible.
7. Do not introduce microservices without a concrete deployment or scaling need.
8. Do not add infrastructure only because it may be useful later.
