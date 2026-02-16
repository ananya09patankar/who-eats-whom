# Backend & Infrastructure Work (Weeks 1–2)

## 1. Architecture Shift Overview
- **Problem**: Frontend-only app pulling directly from iNaturalist (stateless, slow, no caching, no backend).
- **Architecture introduced**:
  - Dockerized data layer (Postgres, Neo4j, Redis) for local dev, mirroring future ITECS Kubernetes (StatefulSets + Deployment).
  - FastAPI backend (`backend/api/`) that acts as the middle layer for the React frontend, replacing direct iNaturalist calls.
  - CSV-driven ETL that loads the curated `observations.csv` into Neo4j (graph data) and Postgres (run metadata + aggregates).
  - Cache invalidation strategy using Redis + `etl_version` from Postgres.
  - Frontend env-based base URL (`VITE_API_BASE_URL`) so the UI can switch to the backend without code changes.
- **Impact**: Adds a stateful backend, formalizes the dual-DB design (Neo4j for graph traversal, Postgres for system state + aggregates), and lays the groundwork for ITECS deployment.

## 2. Infrastructure & Deployment Readiness
- Added `docker-compose.yml` to start Postgres 16, Neo4j 5, and Redis 7 locally with persistent volumes.
- These containers mirror the intended Kubernetes setup (StatefulSets for Postgres/Neo4j, Deployment for Redis) and allow FastAPI + ETL scripts to connect over `localhost`.
- Verified connectivity to all services (`psql`, Neo4j Browser, Redis CLI) to ensure local development environment is consistent.

## 3. FastAPI Backend (`backend/api/`)
- Core endpoints:
  - `GET /health` – basic uptime check.
  - `GET /api/v1/etl/status` – surfaces latest ETL run info from Postgres `etl_runs`, plus `etl_state` (currently storing `etl_version`).
  - `GET /api/v1/species/{taxon}/prey` & `/predators` – run Cypher queries against Neo4j and cache responses in Redis. Cache keys include `etl_version` so new ETL runs invalidate old cache entries automatically.
  - `GET /api/v1/species/{taxon}/prey_pg`, `/predators_pg`, `/summary` – serve top prey/predator lists and diet percentages from Postgres aggregates.
- Support modules:
  - `app/db_pg.py` – Postgres helpers for ETL metadata, aggregates, and cache version retrieval.
  - `app/db_neo4j.py` – Neo4j driver management + Cypher queries.
  - `app/cache.py` – Redis JSON helpers.
  - `app/config.py` – centralizes environment-driven settings (DB DSNs, Redis URI, allowed origins, cache TTL).
  - `.env.example`, `requirements.txt`, and API `Dockerfile` added for reproducibility.

## 4. CSV ETL Loader (`tools/load_csv_to_neo4j.py`)
- Ingests the refined `observations.csv` and derives ~4,015 predator→prey interactions using the "eater" vs "partner observation" fields.
- Writes to both databases per run:
  1. Logs run metadata in Postgres (`etl_runs`) and increments `etl_state.etl_version`.
  2. Populates Neo4j `Species` nodes and `[:EATS]` relationships with counts.
  3. Populates Postgres serving tables `interactions_agg` (per-run predator→prey counts) and `diet_aggregates` (percentages).
- This script is the current ETL implementation; it demonstrates how raw or refined feeds can be ingested and tracked.

## 5. Postgres Schema & Usage
- Tables created:
  - `etl_runs` – run_id, started_at, ended_at, status, JSON details (source file, interactions count, etl_version).
  - `etl_state` – key/value for global ETL state (`etl_version`).
  - `etl_failures` – placeholder for future error logging (currently unused).
  - `interactions_agg` – stores predator_taxon_id, prey_taxon_id, names, counts per run.
  - `diet_aggregates` – stores prey percentages per predator per run.
- All Postgres-backed endpoints read from these tables; the loader and API are the only writers/readers, ensuring a clean contract.

## 6. Neo4j Usage
- Neo4j container holds the `Species` nodes and `[:EATS]` edges loaded by the CSV ETL.
- FastAPI uses Neo4j for traversal-heavy queries (prey, predators, future network/depth queries).
- No manual Cypher beyond the initial constraint (`CREATE CONSTRAINT species_taxon_id IF NOT EXISTS …`); the loader handles inserts/updates.

## 7. Redis Caching
- Cache wrapper stores JSON responses for Neo4j-backed endpoints.
- Cache keys include endpoint name, parameters, and current `etl_version` from Postgres. After each ETL run, `etl_version` increments, so old cache entries become stale automatically.

## 8. Frontend Integration Prep
- Updated `src/utils/api.ts` to read `import.meta.env.VITE_API_BASE_URL` (default `http://localhost:8000`).
- This change decouples the React app from iNaturalist; once components switch to the `/api/v1/…` endpoints, pointing to the backend is just an env change.
- No UI logic was updated yet; this was infrastructure prep.

## 9. Dagster / Future ETL Plan
- Created `backend/etl/` with Dagster project scaffolding (assets, jobs, schedules, resource configs) plus `pyproject.toml` and Dockerfile.
- **Scaffolding** = directory layout, placeholder files, and initial code structure exist, but no Dagster job is active yet. The CSV loader is the only ETL running now.
- Plan: replace CSV ingest with a Dagster/Cron-based pipeline that fetches raw iNaturalist data, applies the external filtering module, and feeds the same Neo4j/Postgres targets. The scaffolding accelerates that transition when ready.

## 10. Demo-Ready Evidence
- `curl` commands against FastAPI show:
  - `/api/v1/etl/status` returning latest run details (run_id, timestamps, `etl_version`, interactions count).
  - `/api/v1/species/243970/prey_pg` returning Postgres-served prey counts.
  - `/api/v1/species/243970/summary` returning diet percentages.
- Neo4j-driven endpoints return the same prey data via graph queries, confirming both DBs are consistent.

## 11. Next Steps
1. **Frontend wiring** – modify React components to consume `/api/v1/...` endpoints; remove direct iNaturalist calls.
2. **Raw iNaturalist ETL** – extend the Dagster scaffold into a real pipeline (or Kubernetes CronJob) that loads raw data, integrates external filtering, and updates Neo4j/Postgres incrementally.
3. **Containerization for ITECS** – build Docker images for API + ETL, create Kubernetes manifests (Deployments, StatefulSets, CronJobs) and deploy to the ITECS-supported cluster with ingress + DNS (Cloudflare/university subdomains).
4. **Monitoring & Documentation** – add runbooks, logs, metrics, and onboarding docs once deployment is in place.
