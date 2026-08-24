# CAT Cost Intelligence demo

An end-to-end procurement cost intelligence demo with three role-based workspaces, shared opportunity evidence, explainable ranking, persistent investigations, and a grounded Vertex AI assistant.

## Start the demo

```bash
cp .env.example .env
python3 backend/synthetic_data_generator.py --output postgres/init/001_seed.sql.gz
docker compose up --build
```

Open [http://localhost:5173](http://localhost:5173). API documentation is at [http://localhost:8000/docs](http://localhost:8000/docs).

Local Compose runs with `RESET_DEMO_DATA_ON_START=true`. Each backend rebuild or restart drops and recreates the prototype schemas from the deterministic synthetic seed before the API starts. The seed keeps its twelve-snapshot history but shifts that history forward so the latest snapshot equals the rebuild timestamp; every executive screen and PDF therefore shows the current **Data as of** date and time. Set reset to `false` in `.env` when you want local workflow changes to persist. Production Compose always disables this reset.

Demo credentials:

| Employee | Username | Role | Password |
|---|---|---|---|
| Sarah Smith | `sarah.smith` | Finance Analyst | `1234` |
| Priya Patel | `priya.patel` | Investigation Expert | `1234` |
| Robert Miller | `robert.miller` | Executive | `1234` |

Authentication is deliberately isolated and demo-only. Replace `backend/app/auth` with production SSO before any real deployment.

## Vertex AI / Gemini

For a complete local walkthrough, see [Local Vertex AI setup for Ask Katty](docs/GCP_VERTEX_AI_LOCAL.md).

The assistant uses `gemini-2.5-flash` through Vertex AI when `GOOGLE_CLOUD_PROJECT` is set and Application Default Credentials are available. Configure `.env`:

```text
GOOGLE_CLOUD_PROJECT=your-project
GOOGLE_CLOUD_LOCATION=global
GOOGLE_GENAI_USE_VERTEXAI=true
GOOGLE_APPLICATION_CREDENTIALS_HOST=/absolute/path/to/application_default_credentials.json
GEMINI_MODEL=gemini-2.5-flash
```

The complete guide uses local Application Default Credentials and explains the Docker mount. Without
cloud configuration, Ask Katty remains usable with deterministic database-grounded answers.

## Generated reports / MinIO

AI-grounded executive PDFs are stored in the `executive-reports` bucket in the local MinIO service.
The application downloads them through an authenticated FastAPI endpoint; MinIO is not exposed
directly to the browser. The object data persists in the `cat_ci_reports` Docker volume even when
the PostgreSQL demo seed is refreshed. The local MinIO console is available at
[http://localhost:9001](http://localhost:9001), using `MINIO_ACCESS_KEY` and
`MINIO_SECRET_KEY` from `.env`.

Reports can be generated from Guidance Home for the enterprise portfolio or from any Product
Detail page for a product-scoped brief. The backend creates the grounded narrative, renders the
PDF, stores it in MinIO, records assistant telemetry, and returns an authenticated download URL.

## Executive information model

Executive Guidance uses one business hierarchy everywhere:

```text
Category (equipment family)
  → Product (equipment model)
    → Component (part)
      → Cost Driver (reason for the gap)
```

Examples of Categories are Excavators, Motor Graders, Wheel Loaders, Dozers, and Off Highway
Trucks. Supplier Price, Logistics & Duties, Tariff, Material, Volume, and Specification Difference
are Cost Drivers—not Categories. Product allocations use one stable primary compatible model so
portfolio totals do not duplicate an opportunity across multiple products.

Executive routes:

```text
/executive
/executive/plants
/executive/products
/executive/products/:productId
/executive/categories
/executive/categories/:categoryId
/executive/components/:componentId
```

Guidance Home includes Ask Katty, backend-ranked priorities and quick wins, and the enterprise
report generator. Product Detail includes Generate report and Send to team actions. Send to team
uses the existing opportunity assignment/investigation lifecycle rather than a parallel workflow.

## Development and verification

```bash
cd backend && uv sync && uv run fastapi dev app/main.py
cd frontend && npm ci && npm run dev
npm --prefix frontend run build
cd backend && PYTHONPATH=. uv run --with pytest pytest -q
docker compose config
```

The seed is deterministic (seed `42`) and contains 500 parts, 27 plants, 100 suppliers, 128 opportunities, 12 monthly snapshots per opportunity, structured cost drivers, persisted ranking results, and workflow records. Regenerating it preserves `OPP-000001` as the stable reference record without introducing application-level special cases. Snapshot timestamps roll forward at startup; business values remain deterministic.

## Architecture

The backend is a FastAPI modular monolith: API → service → repository → PostgreSQL. The React app uses an `AuthContext`, protected role routes, role-specific shells, and a single `SharedOpportunityDetail` for both Finance Analyst and Investigation Expert routes. Executive portfolio queries always select the latest snapshot at or before the requested timestamp and attribute each part to one stable primary compatible product model. Significant workflow transitions append immutable opportunity events. Assistant sessions, interactions, tool calls, and basic API timing are written to the `telemetry` schema.
