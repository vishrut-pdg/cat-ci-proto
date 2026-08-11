# Product Requirements Document (PRD)
## CAT Cost Intelligence Platform

**Version:** 0.1  
**Status:** Draft

## 1. Product Overview

The CAT Cost Intelligence Platform is a role-based cost intelligence and opportunity-management application.

The platform combines:
- product and engineering part data,
- plant and supplier data,
- cost and spend history,
- logistics and tariff data,
- opportunity detection and ranking,
- investigation workflows,
- recommendation creation,
- decision workflows,
- execution tracking,
- outcome measurement.

Core lifecycle:

```text
Part + Plant + Supplier + Cost Context
                |
                v
          Opportunity
                |
                v
          Investigation
                |
                v
        Recommendation
                |
                v
            Decision
                |
                v
           Execution
                |
                v
            Outcome
                |
                v
       RecSys Feedback Loop
```

## 2. Problem Statement

The business needs a structured way to identify and act on cost-saving opportunities across a large number of parts, plants, suppliers, and cost components.

The platform should answer:
- Which parts have abnormal cost variance?
- Which opportunities have the largest potential savings?
- Which plant or supplier is creating the variance?
- Are logistics, tariffs, volume, or specification differences responsible?
- Which expert should investigate an opportunity?
- What recommendations were produced?
- What decision was taken?
- Was the recommendation executed?
- Were expected savings realized?

## 3. Product Objectives

The prototype must:
1. Generate realistic synthetic enterprise data.
2. Store it in PostgreSQL.
3. Expose it through FastAPI.
4. Rank cost-saving opportunities.
5. Explain why an opportunity is ranked highly.
6. Provide role-specific dashboards.
7. Support the lifecycle from opportunity review through execution.
8. Preserve historical metrics and decision context.
9. Provide a foundation for future on-premise Data Lake integration.

## 4. Current Technical Scope

### Frontend
- Astro
- Finance Analyst
- Investigation Expert
- Decision Maker
- Execution
- Process Admin

### Backend
- Python
- FastAPI
- SQLAlchemy Core
- Psycopg 3
- Pydantic

### Database
- PostgreSQL 17 Alpine
- Synthetic seed data loaded at database initialization

### Deferred
- Redis
- pgvector
- Elasticsearch
- MinIO
- Kubernetes
- production authentication / SSO
- live Data Lake integration

## 5. Core Domain Principle

A **Part** is a stable catalog or engineering entity.

An **Opportunity** is a financial or operational condition detected for a part in a business context.

Example:

```text
Part
20R-2009
Cat Reman Hydraulic Pump

Opportunity
OPP-000001
Part: 20R-2009
Plant: Brazil PIR
Unit Cost: $421.32
Peer Average: $366.23
Variance: +15%
Potential Savings: $720K
```

A part may have zero, one, or many opportunities over time.

## 6. User Roles

### Finance Analyst
Responsibilities:
- review opportunities,
- shortlist,
- reject,
- inspect savings,
- compare plants,
- compare suppliers,
- analyze logistics,
- analyze tariffs,
- assign experts,
- monitor outcomes,
- monitor learnings.

### Investigation Expert
Responsibilities:
- investigate assigned opportunities,
- review evidence,
- identify root causes,
- consult experts,
- capture findings,
- create recommendations,
- submit recommendations.

### Decision Maker
Responsibilities:
- approve,
- approve with modification,
- send back,
- escalate,
- reject,
- review approved decisions.

### Execution Owner
Responsibilities:
- execute decisions,
- track progress,
- report blockers,
- request review,
- report realized savings.

### Process Admin
Responsibilities:
- monitor lifecycle,
- identify bottlenecks,
- monitor overdue work,
- monitor outcomes and learnings.

## 7. Primary User Journey

```text
1. RecSys identifies opportunity
2. Finance Analyst reviews
3. Finance Analyst shortlists
4. Finance Analyst assigns expert
5. Expert investigates
6. Expert records findings
7. Expert creates recommendation
8. Recommendation is submitted
9. Decision Maker reviews
10. Decision is approved / modified / sent back / rejected
11. Approved decision goes to execution
12. Execution Owner implements
13. Outcome is measured
14. Outcome feeds future ranking
```

## 8. Finance Analyst Scope

### Opportunity Shortlisting
Show:
- opportunities identified,
- awaiting review,
- potential savings,
- high impact opportunities.

Initial synthetic dataset:
```text
Parts: 500
Plants: 27
Suppliers: 100
Opportunities: 128
Awaiting Review: 32
High Impact: 18
```

### Reference Opportunity
```text
Opportunity ID: OPP-000001
Part Number: 20R-2009
Component ID: HP-100045
Part: Cat Reman Hydraulic Pump
Plant: Brazil PIR
Priority: High
Unit Cost: $421.32
Peer Average: $366.23
Variance: $55.09 / 15%
Potential Savings: $720,000
Impact Score: 92
Confidence: 92%
```

## 9. Opportunity Detail Tabs

### Overview
Required:
- unit cost,
- peer average,
- variance,
- annual volume,
- annual spend,
- potential savings,
- impact score,
- confidence,
- cost drivers.

Reference cost drivers:
```text
Logistics & Duties          6.2%
Supplier Price              4.0%
Lower Volume                2.8%
Specification Difference    2.0%
```

### Plants
Reference:
```text
Brazil     $421.32   +15%
Mexico     $362.11    -1%
USA        $358.79    -2%
India      $348.22    -5%
China      $351.47    -4%
```

### Suppliers
Required:
- supplier,
- country,
- unit cost,
- peer average,
- variance,
- annual spend,
- annual volume,
- performance scores.

### Logistics
Reference:
```text
Ocean Freight          $18.60
Import Duty            $21.30
Local Transport         $7.20
Insurance               $3.40
Packaging               $2.80
Handling & Other        $1.10
Total                   $54.40
Peer Average            $37.50
Variance                $16.90
```

### Tariff
Reference:
```text
HS Code: 8413.91.90
Brazil Duty Rate: 10%
Peer Average Duty Rate: 5.8%
Import Duty / Unit: $42.13
Peer Duty / Unit: $18.40
Annual Duty Impact: $145K
```

## 10. Backend API Requirements

Existing:
```http
GET /api/v1/health
GET /api/v1/opportunities
```

Opportunity detail:
```http
GET /api/v1/opportunities/{opportunity_id}
GET /api/v1/opportunities/{opportunity_id}/overview
GET /api/v1/opportunities/{opportunity_id}/plants
GET /api/v1/opportunities/{opportunity_id}/suppliers
GET /api/v1/opportunities/{opportunity_id}/logistics
GET /api/v1/opportunities/{opportunity_id}/tariff
```

Planned actions:
```http
POST /api/v1/opportunities/{opportunity_id}/shortlist
POST /api/v1/opportunities/{opportunity_id}/reject
POST /api/v1/opportunities/{opportunity_id}/assign
```

Planned investigation APIs:
```http
GET  /api/v1/investigations
GET  /api/v1/investigations/{investigation_id}
POST /api/v1/investigations/{investigation_id}/findings
POST /api/v1/investigations/{investigation_id}/recommendations
POST /api/v1/investigations/{investigation_id}/submit
```

## 11. Recommendation System

V1 pipeline:
```text
Part / Plant Economic Context
           |
           v
    Candidate Generation
           |
           v
       Hard Filters
           |
           v
      Feature Builder
           |
           v
      Base Ranking
           |
           v
   Expert Personalization
           |
           v
      Explanation Layer
```

V1 should use deterministic weighted ranking, not a trained ML model.

Candidate dimensions:
- savings potential,
- cost variance,
- cross-plant variance,
- supplier opportunity,
- logistics opportunity,
- tariff impact,
- historical success,
- data confidence,
- execution feasibility.

The system stores:
- ranking run,
- ranking result,
- score components,
- explanation reasons.

## 12. Explanation Requirements

LLMs must not invent financial facts.

Explanations originate from structured features.

Example:
```json
{
  "reason_code": "HIGH_LOGISTICS_COST",
  "metric_value": 54.40,
  "benchmark_value": 37.50,
  "explanation": "Logistics cost is 45% above the peer average."
}
```

## 13. PostgreSQL Logical Schemas

### catalog
- parts
- part_catalog
- part_attributes
- specification_definitions
- part_specifications
- equipment_models
- part_compatibility

### supply
- plants
- suppliers
- part_supply

### economics
- part_economic_fact

### opportunity
- opportunities
- metric_snapshots
- cost_drivers
- plant_comparisons
- supplier_comparisons
- logistics_components
- logistics_trend
- tariff_details
- tariff_comparisons

### identity_data
- users
- roles
- user_roles
- expert_profiles

### recsys
- ranking_runs
- ranking_results
- ranking_score_components
- recommendation_explanations

### workflow
- investigations
- recommendations
- decisions
- executions
- outcomes

## 14. Synthetic Data Requirements

Synthetic data must:
- be deterministic,
- preserve referential integrity,
- resemble enterprise procurement data,
- contain correlated metrics,
- contain 12 months of history,
- preserve OPP-000001 as the reference case.

Target custom PostgreSQL Docker image:
```text
< 200 MB where practical for the local platform
```

## 15. Architecture Requirements

Dependency direction:
```text
API
 |
Service
 |
Repository
 |
PostgreSQL
```

Rules:
1. Part is not Opportunity.
2. Frontend does not calculate financial business metrics.
3. API layer does not contain SQL.
4. Repository layer does not contain UI logic.
5. RecSys does not invent source facts.
6. Historical snapshots must remain reproducible.
7. Do not introduce microservices without a concrete need.
8. Add infrastructure only when a current requirement needs it.

## 16. Milestones

### Milestone 1 — Synthetic Data
Status: Complete

### Milestone 2 — PostgreSQL
Status: Complete

### Milestone 3 — Backend Foundation
Status: Complete
- DB connection
- health API
- opportunity list API

### Milestone 4 — Opportunity Detail APIs
Status: Current
- detail
- overview
- plants
- suppliers
- logistics
- tariff

### Milestone 5 — RecSys
- filters
- feature builder
- ranking
- score components
- explanations

### Milestone 6 — Frontend Integration
- replace hardcoded data
- connect detail tabs
- shortlist
- reject
- assign

### Milestone 7 — Investigation Workflow
### Milestone 8 — Decision Workflow
### Milestone 9 — Execution and Outcomes
### Milestone 10 — Final Docker Compose

## 17. Prototype Definition of Done

The prototype is complete when a user can:
1. start the environment,
2. view synthetic opportunities,
3. see ranked recommendations,
4. open Hydraulic Pump Brazil,
5. inspect Overview, Plants, Suppliers, Logistics, and Tariff,
6. shortlist,
7. assign an expert,
8. investigate,
9. create a recommendation,
10. submit it,
11. approve it,
12. execute it,
13. record an outcome,
14. use the outcome as future RecSys feedback.
