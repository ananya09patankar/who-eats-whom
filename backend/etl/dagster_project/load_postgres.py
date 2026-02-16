import json
import psycopg

def log_run(pg_dsn: str, run_id: str, status: str, details: dict, ended: bool=False) -> None:
    with psycopg.connect(pg_dsn) as conn:
        with conn.cursor() as cur:
            if not ended:
                cur.execute(
                    "INSERT INTO etl_runs(run_id, started_at, status, details) VALUES (%s, now(), %s, %s::jsonb) "
                    "ON CONFLICT (run_id) DO NOTHING",
                    (run_id, status, json.dumps(details)),
                )
            else:
                cur.execute(
                    "UPDATE etl_runs SET ended_at = now(), status=%s, details=%s::jsonb WHERE run_id=%s",
                    (status, json.dumps(details), run_id),
                )
        conn.commit()

def get_state(pg_dsn: str, key: str, default: str="") -> str:
    with psycopg.connect(pg_dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT value FROM etl_state WHERE key=%s", (key,))
            row = cur.fetchone()
            return row[0] if row else default

def set_state(pg_dsn: str, key: str, value: str) -> None:
    with psycopg.connect(pg_dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO etl_state(key, value) VALUES (%s,%s) "
                "ON CONFLICT (key) DO UPDATE SET value=excluded.value",
                (key, value),
            )
        conn.commit()
