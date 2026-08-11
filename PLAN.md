Current repo is already a good starting point:

```text
CAT-CI-PROTO/
├── backend/
│   ├── .venv/
│   ├── main.py
│   ├── pyproject.toml
│   └── ...
│
├── frontend/
│   └── Astro application
│
├── data-seed.sh
├── docker-compose.yaml
└── README.md
```

I recommend this implementation plan.

1. **Freeze the V1 scope and infrastructure.** For the first working version, use `Astro + FastAPI + PostgreSQL + Redis`. Do not introduce Elasticsearch, Kafka, MinIO, Kubernetes, or separate RecSys microservices yet. They fit the future architecture, but they create unnecessary integration work before we know the actual access patterns. The local architecture should be:

```text
┌──────────────┐
│ Astro        │
│ :4321        │
└──────┬───────┘
       │ HTTP
       ▼
┌──────────────┐
│ FastAPI      │
│ :8000        │
└──────┬───────┘
       │
       ├──────────────► Redis :6379
       │
       ▼
┌──────────────┐
│ PostgreSQL   │
│ :5432        │
└──────────────┘
```

`docker-compose.yaml` starts PostgreSQL, Redis, and optionally the backend. During active frontend/backend development, you can still run Astro and FastAPI directly on the host.

2. **Refactor the backend before adding business logic.** Move away from a single `main.py`. I would target this:

```text
backend/
├── app/
│   ├── main.py
│   ├── config.py
│   │
│   ├── api/
│   │   ├── router.py
│   │   └── v1/
│   │       ├── health.py
│   │       ├── opportunities.py
│   │       ├── parts.py
│   │       ├── investigations.py
│   │       ├── experts.py
│   │       ├── decisions.py
│   │       └── executions.py
│   │
│   ├── db/
│   │   ├── base.py
│   │   ├── session.py
│   │   └── models/
│   │
│   ├── schemas/
│   │   ├── opportunity.py
│   │   ├── part.py
│   │   ├── investigation.py
│   │   └── recommendation.py
│   │
│   ├── repositories/
│   │   ├── opportunity.py
│   │   ├── part.py
│   │   └── investigation.py
│   │
│   ├── services/
│   │   ├── opportunity_service.py
│   │   ├── investigation_service.py
│   │   └── assignment_service.py
│   │
│   └── recsys/
│       ├── candidate_generator.py
│       ├── filters.py
│       ├── features.py
│       ├── ranker.py
│       ├── explanations.py
│       └── models.py
│
├── migrations/
├── tests/
├── pyproject.toml
└── Dockerfile
```

The important architecture is:

```text
API Router
    ↓
Service
    ↓
Repository
    ↓
Database
```

The API layer should never contain ranking calculations or raw SQL.

3. **Implement only the database tables needed for the current UI first.** We designed a larger enterprise model, but V1 should be smaller. Start with:

```text
parts
part_catalog
part_attributes
part_specifications
part_compatibility

plants
suppliers
part_supply

part_economic_fact

opportunities
opportunity_metric_snapshots
opportunity_cost_drivers
opportunity_plant_comparisons
opportunity_supplier_comparisons

users
roles
user_roles

investigations
investigation_experts
investigation_findings
recommendations

ranking_runs
ranking_results
ranking_score_components

opportunity_events
```

Then add `decisions`, `executions`, and `outcomes` when we wire those dashboards.

Use **SQLAlchemy models + Alembic migrations**. Do not let `data-seed.sh` create schema manually. The correct sequence should become:

```text
docker compose up
        ↓
Alembic migration
        ↓
data-seed.sh
        ↓
FastAPI starts
```

4. **Create one coherent seed dataset rather than lots of unrelated dummy records.** The most important seed object should be Hydraulic Pump Brazil because all of your screens already revolve around it.

```text
Part
20R-2009 / HP-100045
Hydraulic Pump
        │
        ├── Brazil PIR
        │     └── Supplier A
        │
        ├── Mexico MAQ
        │
        ├── USA LLC
        │
        ├── India TPL
        │
        └── China XUZ
        │
        ├── monthly cost history
        ├── monthly volume history
        ├── logistics costs
        ├── tariff costs
        ├── supplier prices
        └── peer benchmarks
```

Then seed another 10–20 opportunities for the shortlisting table.

For example:

```text
Hydraulic Pump              Brazil       $720K
Engine Control Module       USA          $480K
Transmission Assembly       China        $390K
Final Drive Motor           India        $260K
Hydraulic Cylinder          Germany      $180K
...
```

All dashboard numbers should ultimately be calculated from this dataset rather than manually repeated across APIs.

5. **Build the opportunity API before building the RecSys.** First make the current screens data-driven.

The first API set should be approximately:

```http
GET /api/v1/opportunities

GET /api/v1/opportunities/{opportunity_id}

GET /api/v1/opportunities/{opportunity_id}/overview

GET /api/v1/opportunities/{opportunity_id}/plants

GET /api/v1/opportunities/{opportunity_id}/suppliers

GET /api/v1/opportunities/{opportunity_id}/logistics

GET /api/v1/opportunities/{opportunity_id}/tariff

POST /api/v1/opportunities/{opportunity_id}/shortlist

POST /api/v1/opportunities/{opportunity_id}/reject
```

For example:

```text
GET /opportunities/OPP-001/overview
```

should provide everything required for:

```text
Hydraulic Pump - Brazil

Cost Variance
15%

Potential Savings
$720K

Unit Cost
$421.32

Peer Average
$366.23

Top Cost Drivers
...
```

The frontend should not reproduce these calculations.

6. **Connect the Finance Analyst screens first.** This becomes our first end-to-end vertical slice:

```text
PostgreSQL
    ↓
FastAPI
    ↓
GET /opportunities
    ↓
Astro
    ↓
Opportunity Shortlisting
    ↓
View Details
    ↓
Hydraulic Pump
    ↓
Overview / Plants / Suppliers / Logistics / Tariff
```

At this point the page you already built becomes a real application.

The sequence I would use is:

```text
Opportunity Shortlisting
        ↓
Overview
        ↓
Plants
        ↓
Suppliers
        ↓
Logistics
        ↓
Tariff
```

Do one tab at a time.

Do **not** connect all screens simultaneously.

7. **Then implement RecSys V1 as a backend module, not a separate microservice.** Once the raw opportunity data is reliable, add:

```text
app/recsys/
├── candidate_generator.py
├── filters.py
├── features.py
├── ranker.py
└── explanations.py
```

The pipeline becomes:

```text
All Part × Plant combinations
            ↓
    Candidate Generation
            ↓
        Hard Filters
            ↓
       Feature Builder
            ↓
        Base Ranking
            ↓
      Opportunity List
            ↓
       Explanation
```

For V1, use an explainable weighted model:

```text
Opportunity Score
 =
    savings potential
  + cost variance
  + plant variance
  + logistics variance
  + supplier variance
  + tariff impact
  + data confidence
```

Example:

```text
Hydraulic Pump Brazil

Potential Savings      0.94 × 30%
Cost Variance          0.91 × 20%
Plant Variance         0.87 × 15%
Logistics              0.93 × 15%
Supplier               0.72 × 10%
Tariff                  0.85 × 5%
Data Quality            0.96 × 5%
                           ───────
Final Score                0.897
```

Then store the result:

```text
ranking_runs

ranking_results

ranking_score_components
```

Now the dashboard's `AI Confidence` and ranking order are no longer arbitrary frontend values.

8. **Build explanation generation from structured reasons.** Before adding an LLM, create deterministic explanation objects:

```json
{
  "opportunity_id": "OPP-001",
  "score": 89.7,
  "reasons": [
    {
      "code": "HIGH_LOGISTICS_COST",
      "value": 54.40,
      "peer_value": 37.50,
      "impact": 16.90
    },
    {
      "code": "HIGH_IMPORT_DUTY",
      "value": 21.30,
      "peer_value": 15.10,
      "impact": 6.20
    }
  ]
}
```

The UI can turn this into:

```text
AI INVESTIGATION PARTNER

Logistics and duties contribute $54.40 per unit,
45% above the peer average.

Top contributors:
• Ocean freight
• Import duties
• Local transport
```

Later an LLM can rewrite this structured explanation. The numbers must still originate from the database/RecSys.

9. **Then connect Shortlist → Assign Expert → Investigation Expert.** This is the second vertical slice.

```text
Finance Analyst
     │
     │ Shortlist
     ▼
Opportunity
SHORTLISTED
     │
     │ Assign Expert
     ▼
Investigation
     │
     ├── opportunity_id
     ├── owner_user_id
     ├── due_date
     └── status = ASSIGNED
     │
     ▼
Investigation Expert Dashboard
     │
     ▼
My Investigations
     │
     ▼
Hydraulic Pump Investigation
```

The relevant APIs become:

```http
POST /api/v1/opportunities/{id}/assign

GET /api/v1/investigations

GET /api/v1/investigations/{id}

POST /api/v1/investigations/{id}/findings

POST /api/v1/investigations/{id}/recommendations

POST /api/v1/investigations/{id}/submit
```

This gets us from discovery to a real recommendation.

10. **Only after that, wire Decision Maker → Execution → Outcome.** That gives the complete lifecycle:

```text
IDENTIFIED
    ↓
AWAITING_REVIEW
    ↓
SHORTLISTED
    ↓
ASSIGNED
    ↓
UNDER_INVESTIGATION
    ↓
RECOMMENDATION_READY
    ↓
SUBMITTED_FOR_DECISION
    ↓
APPROVED
    ↓
IN_EXECUTION
    ↓
MONITORING
    ↓
COMPLETED
```

Every transition writes an `opportunity_events` record.

That event history will later power the Process Admin dashboard without us creating another unrelated data model.

### The development order I recommend

```text
PHASE 1
Infrastructure
Postgres + Redis + FastAPI + Astro
        ↓

PHASE 2
Database models + Alembic
        ↓

PHASE 3
Hydraulic Pump seed dataset
        ↓

PHASE 4
Opportunity APIs
        ↓

PHASE 5
Finance Analyst frontend integration
        ↓

PHASE 6
RecSys candidate generation + filtering
        ↓

PHASE 7
Ranking + score explanations
        ↓

PHASE 8
Expert assignment
        ↓

PHASE 9
Investigation Expert workflow
        ↓

PHASE 10
Decision Maker workflow
        ↓

PHASE 11
Execution + outcomes
        ↓

PHASE 12
Feedback → ranking
        ↓

PHASE 13
Redis caching / batch jobs
        ↓

PHASE 14
Kubernetes deployment
```

One architectural point I would keep strict: **Kubernetes and microservice extraction come last, not first.** Build the FastAPI application as a modular monolith whose modules already have clean boundaries. Once we know which services need independent scaling, they can be extracted cleanly:

```text
FastAPI modular monolith V1
          │
          ├── opportunity
          ├── investigation
          ├── workflow
          └── recsys
                 │
                 ▼ later
        Kubernetes services
          ├── API
          ├── RecSys
          ├── Worker
          └── Scheduler
```

For our **next coding step**, I would start with only **Phase 1 + Phase 2**: clean up `docker-compose.yaml`, establish PostgreSQL/Redis connectivity, restructure FastAPI, configure SQLAlchemy + Alembic, and create the first core models. Once that boots correctly, we move to `data-seed.sh` and the Hydraulic Pump dataset.
