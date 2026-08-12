# CAT Cost Intelligence demo

An end-to-end procurement cost intelligence demo with two role-based workflows, shared opportunity evidence, explainable ranking, persistent investigations, and a grounded Vertex AI assistant.

## Start the demo

```bash
cp .env.example .env
python3 backend/synthetic_data_generator.py --output postgres/init/001_seed.sql.gz
docker compose up --build
```

Open [http://localhost:5173](http://localhost:5173). API documentation is at [http://localhost:8000/docs](http://localhost:8000/docs).

Demo credentials:

| Employee | Role | Password |
|---|---|---|
| Sarah Smith | Finance Analyst | `1234` |
| Priya Patel | Investigation Expert | `1234` |

Authentication is deliberately isolated and demo-only. Replace `backend/app/auth` with production SSO before any real deployment.

## Vertex AI / Gemini

The assistant uses `gemini-2.5-flash` through Vertex AI when `GOOGLE_CLOUD_PROJECT` is set and Application Default Credentials are available. Configure `.env`:

```text
GOOGLE_CLOUD_PROJECT=your-project
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS_HOST=/absolute/path/to/service-account.json
GEMINI_MODEL=gemini-2.5-flash
```

For a service-account file, mount it into the backend container and point `GOOGLE_APPLICATION_CREDENTIALS` at the mounted path; never copy credentials into an image. Without cloud configuration, the endpoint remains usable with a deterministic, database-grounded summary for local demos.

### Docker service-account setup

1. Enable billing and the Vertex AI API in the selected Google Cloud project.
2. Create a service account and grant it `roles/aiplatform.user`.
3. Download a JSON key for demo/local use and keep it outside Git.
4. Set `GOOGLE_APPLICATION_CREDENTIALS_HOST` in `.env` to the absolute host path of the JSON file. Docker mounts it read-only at the path expected by the backend. If omitted, Compose uses the standard gcloud ADC file.
5. Set `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION=us-central1`, and `GOOGLE_GENAI_USE_VERTEXAI=true` in `.env`.
6. Recreate the backend with `docker compose up -d --build --force-recreate backend frontend`.

For local backend execution outside Docker, prefer Application Default Credentials:
`gcloud auth application-default login`. Do not commit a service-account key.

## Development and verification

```bash
cd backend && uv sync && uv run fastapi dev app/main.py
cd frontend && npm ci && npm run dev
npm --prefix frontend run build
python3 -m compileall -q backend/app
docker compose config
```

The seed is deterministic (seed `42`) and contains 500 parts, 27 plants, 100 suppliers, 128 opportunities, 12 monthly snapshots per opportunity, persisted ranking results, and workflow records. Regenerating it preserves `OPP-000001` as the stable reference record without introducing application-level special cases.

## Architecture

The backend is a FastAPI modular monolith: API → service → repository → PostgreSQL. The React app uses an `AuthContext`, protected role routes, role-specific shells, and a single `SharedOpportunityDetail` for both Finance Analyst and Investigation Expert routes. Significant workflow transitions append immutable opportunity events. Assistant sessions, interactions, tool calls, and basic API timing are written to the `telemetry` schema.
