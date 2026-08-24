# CAT Cost Intelligence backend

FastAPI backend for the Finance Analyst, Investigation Expert, and Executive Guidance workspaces.
It is a modular monolith with the flow `API → service → repository → PostgreSQL`; financial
aggregation is never performed by React or the language model.

## Run locally

The supported full-stack workflow is from the repository root:

```bash
cp .env.example .env
docker compose up --build
```

For backend-only development, provide a reachable PostgreSQL `DATABASE_URL`, then run:

```bash
uv sync
uv run fastapi dev app/main.py
```

The API is available at `http://localhost:8000`; OpenAPI documentation is at
`http://localhost:8000/docs`.

## Demo database refresh

When `RESET_DEMO_DATA_ON_START=true`, `docker-entrypoint.sh` runs `app.db.demo_seed` before Uvicorn.
The destructive local refresh:

1. drops and recreates the prototype schemas from `001_seed.sql.gz`;
2. seeds the Executive role and Robert Miller from `002_executive_role.sql`;
3. creates and maps equipment categories from `003_equipment_categories.sql`;
4. starts from the same deterministic twelve metric snapshots.

After the optional reset, `app.db.runtime_migrations` always applies the idempotent Executive-role
and equipment-taxonomy SQL. This is required for existing production volumes because PostgreSQL
does not rerun `/docker-entrypoint-initdb.d` after initial volume creation. When
`ROLL_DEMO_SNAPSHOTS_ON_START=true`, the same startup step shifts the twelve-point history so its
newest snapshot equals the current startup timestamp. Set reset to `false` if workflow changes
should survive backend restarts.

The migration is non-destructive and safe to rerun:

```bash
uv run python -m app.db.runtime_migrations
```

## Executive semantics

Use these terms consistently in repositories, schemas, prompts, and reports:

- **Category**: equipment family, such as Excavators, Dozers, or Wheel Loaders.
- **Product**: a specific equipment model.
- **Component**: a part used by one or more products.
- **Cost Driver**: the reason for cost variance, such as Supplier Price, Logistics & Duties,
  Tariff, Material, Volume, or Specification Difference.

`catalog.parts.category` is treated as a part classification, not an executive equipment category.
Equipment categories are stored in `catalog.equipment_categories` and referenced by
`catalog.equipment_models.category_id`.

## Executive API

All endpoints require the `EXECUTIVE` role.

```text
GET  /api/v1/executive/summary
GET  /api/v1/executive/quick-wins
GET  /api/v1/executive/plants
GET  /api/v1/executive/products
GET  /api/v1/executive/products/{product_id}
GET  /api/v1/executive/products/{product_id}/trend
GET  /api/v1/executive/products/{product_id}/cost-drivers
GET  /api/v1/executive/categories
GET  /api/v1/executive/components/{component_id}
GET  /api/v1/executive/report
GET  /api/v1/executive/reports/{report_id}/download
POST /api/v1/assistant/executive/chat
POST /api/v1/assistant/executive/report
```

Common filters include `as_of_date`, `period`, `scope`, `region`, `plant_id`, `product_id`, and
`category_id`. Analytical queries choose one latest valid snapshot per opportunity. Product
aggregation assigns each part to one stable primary compatible model to prevent duplicated savings.

## Ask Katty and reports

Persona prompts are separated for Finance Analyst, Investigation Expert, Executive, and Executive
Report use cases. Executive evidence explicitly distinguishes equipment categories from cost
drivers and distinguishes all attributed opportunities from high-priority opportunities.

Vertex AI is used when `GOOGLE_CLOUD_PROJECT` and Application Default Credentials are configured;
otherwise the service returns deterministic grounded responses. See
[`../docs/GCP_VERTEX_AI_LOCAL.md`](../docs/GCP_VERTEX_AI_LOCAL.md).

Generated PDFs are rendered with ReportLab and stored in MinIO. Product-scoped report generation
removes portfolio-only filters before repository calls, and failures are logged with their complete
traceback. The browser downloads reports through the authenticated FastAPI download endpoint.

## Tests

```bash
.venv/bin/python -m unittest discover -s tests -v
```

The suite covers executive authentication, prompt separation, typed nullable SQL filters,
current-timestamp resolution, invalid scopes, and the product-scoped report regression path.
