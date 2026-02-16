import os
import re
import csv
import uuid
from collections import defaultdict
from datetime import datetime, timezone
import psycopg
from neo4j import GraphDatabase

CSV_PATH = os.getenv("CSV_PATH", "observations.csv")

PG_DSN = os.getenv("PG_DSN", "postgresql://wew:wewpass@localhost:5432/wew")
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASS = os.getenv("NEO4J_PASS", "neo4jpass")

PARTNER_RE = re.compile(r"/observations/(\d+)")

def extract_partner_id(url: str) -> str | None:
    if not url:
        return None
    m = PARTNER_RE.search(url)
    return m.group(1) if m else None

def bump_etl_version(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT value FROM etl_state WHERE key='etl_version'")
        row = cur.fetchone()
        v = int(row[0]) if row else 0
        v += 1
        cur.execute("""
            INSERT INTO etl_state(key, value) VALUES ('etl_version', %s)
            ON CONFLICT (key) DO UPDATE SET value=excluded.value
        """, (str(v),))
    conn.commit()
    return v

def main():
    if not os.path.exists(CSV_PATH):
        raise SystemExit(f"CSV not found at: {CSV_PATH}")

    run_id = str(uuid.uuid4())
    started = datetime.now(timezone.utc)

    # Load all rows into memory indexed by observation id (CSV column 'id')
    rows_by_obs_id: dict[str, dict] = {}
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            obs_id = row.get("id")
            if obs_id:
                rows_by_obs_id[obs_id] = row

    # Prepare interactions by pairing eater row -> partner row (prey)
    interactions: list[tuple[int, int, str, str]] = []
    # tuple: (pred_taxon_id, prey_taxon_id, pred_name, prey_name)
    for obs_id, row in rows_by_obs_id.items():
        role = (row.get('field:id meant for "eater" or organism being eaten?') or "").strip().lower()
        if role != "eater":
            continue

        partner_url = row.get('field:url for "partner" observation') or ""
        partner_obs_id = extract_partner_id(partner_url)
        if not partner_obs_id:
            continue

        partner_row = rows_by_obs_id.get(partner_obs_id)
        if not partner_row:
            continue

        pred_taxon = row.get("taxon_id")
        prey_taxon = partner_row.get("taxon_id")
        if not pred_taxon or not prey_taxon:
            continue

        pred_sci = (row.get("scientific_name") or "").strip()
        pred_common = (row.get("common_name") or "").strip()
        prey_sci = (partner_row.get("scientific_name") or "").strip()
        prey_common = (partner_row.get("common_name") or "").strip()

        pred_name = pred_sci or pred_common or ""
        prey_name = prey_sci or prey_common or ""

        interactions.append((int(pred_taxon), int(prey_taxon), pred_name, prey_name))

    print(f"Loaded {len(rows_by_obs_id)} observations")
    print(f"Derived {len(interactions)} predator→prey interactions from eater/partner links")

    # Write to Postgres: log run start
    with psycopg.connect(PG_DSN) as pg:
        with pg.cursor() as cur:
            cur.execute("""
                INSERT INTO etl_runs(run_id, started_at, status, details)
                VALUES (%s, now(), %s, %s::jsonb)
            """, (run_id, "RUNNING", '{"source":"observations.csv"}'))
        pg.commit()

        # Write to Neo4j
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
        cypher = """
        MERGE (pred:Species {taxon_id: $pred_id})
          ON CREATE SET pred.name = $pred_name
          ON MATCH SET pred.name = CASE WHEN pred.name IS NULL OR pred.name = "" THEN $pred_name ELSE pred.name END
        MERGE (prey:Species {taxon_id: $prey_id})
          ON CREATE SET prey.name = $prey_name
          ON MATCH SET prey.name = CASE WHEN prey.name IS NULL OR prey.name = "" THEN $prey_name ELSE prey.name END
        MERGE (pred)-[r:EATS]->(prey)
          ON CREATE SET r.count = 1
          ON MATCH SET r.count = r.count + 1
        """
        with driver.session() as session:
            # batch in chunks to avoid huge transaction
            CHUNK = 1000
            for i in range(0, len(interactions), CHUNK):
                batch = interactions[i:i+CHUNK]
                tx = session.begin_transaction()
                for pred_id, prey_id, pred_name, prey_name in batch:
                    tx.run(cypher, pred_id=pred_id, prey_id=prey_id, pred_name=pred_name, prey_name=prey_name)
                tx.commit()
        driver.close()

        # bump etl_version for cache keying
        new_ver = bump_etl_version(pg)

        # Mark run success
        with pg.cursor() as cur:
            cur.execute("""
                UPDATE etl_runs
                SET ended_at = now(), status = %s, details = %s::jsonb
                WHERE run_id = %s
            """, ("SUCCESS", f'{{"source":"observations.csv","etl_version":{new_ver},"interactions":{len(interactions)}}}', run_id))
        pg.commit()

    print("Loaded into Neo4j and updated Postgres etl_runs/etl_state(etl_version).")

if __name__ == "__main__":
    main()
