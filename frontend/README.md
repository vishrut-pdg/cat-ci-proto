# CAT Cost Intelligence frontend

React 19, TypeScript, Vite, and React Router frontend for the role-based CAT Cost Intelligence
demo. API access is centralized in `src/services`; executive pages do not contain independent
financial calculations or screen-specific mock values.

## Run locally

For the complete application, run from the repository root:

```bash
cp .env.example .env
docker compose up --build
```

For frontend development against an API at `http://localhost:8000`:

```bash
npm ci
npm run dev
```

The Vite app is available at `http://localhost:5173`. `VITE_API_BASE_URL` defaults to `/api/v1` in
the containerized build.

## Executive routes

```text
/executive                         Guidance Home, Ask Katty, quick wins, report generator
/executive/plants                  Plant comparison
/executive/products                Product comparison with equipment-category filter
/executive/products/:productId     Product detail, trend, cost drivers, report/team actions
/executive/categories              Equipment-category ranking
/executive/categories/:categoryId  Category summary and product drill-down
/executive/components/:componentId Component opportunity brief
```

The UI uses the hierarchy **Category → Product → Component → Cost Driver**. Category means equipment
family; Logistics, Tariff, Material, Supplier Price, Volume, and similar terms are displayed only
as cost drivers. All drill-downs use generic IDs from React Router.

## Data freshness

API responses include the latest snapshot timestamp. `ExecutiveFilters` formats it using the
browser's local timezone and shows both current date and time. With demo reset enabled, backend
startup rolls the twelve-snapshot history forward, so the displayed **Data as of** timestamp follows
each rebuild rather than remaining fixed at 12 Jun 2026.

## Ask Katty and generated reports

Guidance Home contains the executive chat, four suggested prompts, and enterprise report generator.
Product Detail contains **Generate report** and **Send to team** actions. Generated PDFs are stored
in MinIO by the backend and downloaded through an authenticated API URL; the frontend never talks
to MinIO directly.

## Build and verification

```bash
npm run build
npm run lint
```

`npm run build` runs the TypeScript project build before Vite creates the production bundle.
