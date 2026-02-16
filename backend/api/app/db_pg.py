import psycopg
from .config import PG_DSN


def get_etl_status() -> dict:
    """
    Returns last ETL run status + current cursor/state if present.
    Works even if ETL isn't implemented yet.
    """
    out = {
        "latest_run": None,
        "state": {}
    }
    with psycopg.connect(PG_DSN) as conn:
        with conn.cursor() as cur:
            # latest run
            cur.execute("""
                SELECT run_id, started_at, ended_at, status, details
                FROM etl_runs
                ORDER BY started_at DESC
                LIMIT 1
            """)
            row = cur.fetchone()
            if row:
                out["latest_run"] = {
                    "run_id": row[0],
                    "started_at": row[1].isoformat() if row[1] else None,
                    "ended_at": row[2].isoformat() if row[2] else None,
                    "status": row[3],
                    "details": row[4],
                }

            # all state keys
            cur.execute("SELECT key, value FROM etl_state")
            for k, v in cur.fetchall():
                out["state"][k] = v
    return out

def get_cache_version() -> str:
    """
    Cache version ties cache to ETL state. If no ETL yet, returns '0'.
    If you later store a key like etl_version or last_successful_run, we use it automatically.
    """
    with psycopg.connect(PG_DSN) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT value FROM etl_state WHERE key='etl_version'")
            row = cur.fetchone()
            return row[0] if row else "0"




def get_latest_run_id() -> str | None:
    with psycopg.connect(PG_DSN) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT run_id
                FROM etl_runs
                WHERE status='SUCCESS'
                ORDER BY started_at DESC
                LIMIT 1
            """)
            row = cur.fetchone()
            return row[0] if row else None

def get_diet_summary(predator_taxon_id: int, limit: int = 20) -> dict:
    run_id = get_latest_run_id()
    if not run_id:
        return {"run_id": None, "predator_taxon_id": predator_taxon_id, "summary": []}

    with psycopg.connect(PG_DSN) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT prey_taxon_id, prey_name, count, pct
                FROM diet_aggregates
                WHERE run_id=%s AND predator_taxon_id=%s
                ORDER BY count DESC
                LIMIT %s
            """, (run_id, predator_taxon_id, limit))
            rows = cur.fetchall()

    summary = [
        {"prey_taxon_id": r[0], "prey_name": r[1], "count": r[2], "pct": r[3]}
        for r in rows
    ]
    return {"run_id": run_id, "predator_taxon_id": predator_taxon_id, "summary": summary}


def get_prey_from_pg(predator_taxon_id: int, limit: int = 50) -> dict:
    """Returns prey list from Postgres interactions_agg (counts)."""
    run_id = get_latest_run_id()
    if not run_id:
        return {"run_id": None, "predator_taxon_id": predator_taxon_id, "prey": []}

    with psycopg.connect(PG_DSN) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT prey_taxon_id, prey_name, count
                FROM interactions_agg
                WHERE run_id=%s AND predator_taxon_id=%s
                ORDER BY count DESC
                LIMIT %s
            """, (run_id, predator_taxon_id, limit))
            rows = cur.fetchall()

    prey = [{"taxon_id": r[0], "name": r[1], "count": r[2]} for r in rows]
    return {"run_id": run_id, "predator_taxon_id": predator_taxon_id, "prey": prey}


def get_predators_from_pg(prey_taxon_id: int, limit: int = 50) -> dict:
    """Returns predators list from Postgres interactions_agg (reverse lookup)."""
    run_id = get_latest_run_id()
    if not run_id:
        return {"run_id": None, "prey_taxon_id": prey_taxon_id, "predators": []}

    with psycopg.connect(PG_DSN) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT predator_taxon_id, predator_name, count
                FROM interactions_agg
                WHERE run_id=%s AND prey_taxon_id=%s
                ORDER BY count DESC
                LIMIT %s
            """, (run_id, prey_taxon_id, limit))
            rows = cur.fetchall()

    predators = [{"taxon_id": r[0], "name": r[1], "count": r[2]} for r in rows]
    return {"run_id": run_id, "prey_taxon_id": prey_taxon_id, "predators": predators}
