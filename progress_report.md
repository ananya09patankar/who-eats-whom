# Backend & Infrastructure Progress (Weeks 1–2)

## 1. Local Infrastructure & Data Services
- Added `docker-compose.yml` to run **Postgres 16**, **Neo4j 5**, and **Redis 7** locally with persistent volumes, mirroring what will later be deployed on ITECS Kubernetes (StatefulSets for Postgres/Neo4j, Deployment for Redis).
- Confirmed connectivity from host to containers (`localhost:5432/7474/7687/6379`) to ensure FastAPI and ETL can talk to these services without extra tooling.

## 2. FastAPI Backend (`backend/api/`)
- Built a container-ready FastAPI service with:
  - `/health`
  - `/api/v1/etl/status` – reads Postgres tables `etl_runs` + `etl_state` to report latest ETL run, status, timestamps, and the cache version.
  - `/api/v1/species/{taxon_id}/prey` + `/predators` – graph-native Neo4j queries cached in Redis; cache keys include `etl_version` so new loads invalidate stale data automatically.
  - `/api/v1/species/{taxon_id}/prey_pg`, `/predators_pg`, `/summary` – Postgres-backed endpoints serving pre-aggregated prey/predator lists and diet percentages for fast UI consumption.
- Supporting modules:
  - `app/db_neo4j.py` – encapsulates Cypher queries and driver management.
  - `app/db_pg.py` – encapsulates SQL queries for ETL metadata, aggregates, and cache version.
  - `app/cache.py` – Redis helper with TTL support.
  - `app/config.py` – centralizes env-driven configuration (DB DSNs, Redis URL, allowed origins).
  - `tools/load_csv_to_neo4j.py` – ETL entrypoint.
- Added `.env.example`, `requirements.txt`, and API `Dockerfile` for portability.

## 3. CSV ETL Loader (`backend/api/tools/load_csv_to_neo4j.py`)
- Ingests `observations.csv` (~10k rows) and derives **4,015 predator→prey interactions** using the "eater" vs "partner observation" fields.
- For each run:
  1. Logs start/run metadata into Postgres `etl_runs` (run_id, timestamps, status, JSON details).
  2. Populates **Neo4j** `Species` nodes and `[:EATS]` relationships (with `count` and `name`).
  3. Writes **Postgres serving tables**:
     - `interactions_agg` (run_id, predator_taxon_id, prey_taxon_id, names, count).
     - `diet_aggregates` (same + `pct`).
  4. Updates `etl_state` with incremented `etl_version`; Redis cache keys use this version to invalidate old entries automatically.
- This makes Postgres the system-of-record for ETL state and fast summaries, while Neo4j remains the graph datastore.

## 4. Frontend Readiness
- `src/utils/api.ts` now reads `import.meta.env.VITE_API_BASE_URL` (fallback `http://localhost:8000`), so the React app can be pointed at our backend by setting one env variable. No UI refactors were done yet—the change simply removes the hardcoded iNaturalist base URL.

## 5. Dagster / Raw iNaturalist Plan (Scaffolding)
- Created `backend/etl/` with Dagster project structure (`assets.py`, `jobs.py`, `schedules.py`, etc.) plus `pyproject.toml` and `Dockerfile`.
- **Scaffolding** means the directory layout and starter modules exist, but no Dagster job is running yet. The CSV loader is the active ETL; Dagster will be used later when we fetch raw iNaturalist data and plug in upstream filtering.

## 6. Demo-Ready Outputs
- `curl` commands show working endpoints:
  - `GET /api/v1/etl/status` → latest run metadata (`etl_version`=1, ~4k interactions).
  - `GET /api/v1/species/243970/prey_pg` → Postgres-served prey list with counts.
  - `GET /api/v1/species/243970/summary` → diet percentages.
- Neo4j queries via the API (`/prey`) show the same data from the graph side, proving both DBs are synchronized.

## 7. Next Steps / Plan
1. **Frontend Integration** – update React components to call `/api/v1/...` endpoints and remove direct iNaturalist calls. The infrastructure hooks are already in place via `VITE_API_BASE_URL`.
2. **Raw iNaturalist ETL** – replace the CSV loader with a cron/Dagster job that fetches raw data, applies the upstream filtering module, and reuses the same Neo4j/Postgres targets.
3. **Containerization & ITECS Deployment** – build Docker images for API + ETL, write Kubernetes manifests (Deployment for API, CronJob for ETL, StatefulSets for Postgres/Neo4j, Deployment for Redis), and deploy onto the ITECS-supported cluster with ingress + DNS.
4. **Monitoring & Documentation** – add runbooks, metric collection, and onboarding docs once the deployment stabilizes.

This document summarizes all backend/infra work completed in the first two weeks.
