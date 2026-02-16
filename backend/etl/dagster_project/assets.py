import asyncio
from dagster import asset, AssetExecutionContext
from .resources import load_config
from .inat_client import fetch_observations
from .filtering import refine_observations
from .transform import to_interactions
from .load_neo4j import load_to_neo4j
from .load_postgres import log_run, get_state, set_state

@asset
def inat_raw(context: AssetExecutionContext) -> list[dict]:
    cfg = load_config()
    run_id = context.run_id
    log_run(cfg.pg_dsn, run_id, "RUNNING", {"stage": "fetch"})

    page = int(get_state(cfg.pg_dsn, "inat_page", "1"))
    data = asyncio.run(fetch_observations(page=page, per_page=200))
    results = data.get("results", [])

    set_state(cfg.pg_dsn, "inat_page", str(page + 1))

    log_run(cfg.pg_dsn, run_id, "RUNNING", {"stage": "fetched", "count": len(results), "page": page})
    context.add_output_metadata({"count": len(results), "page": page})
    return results

@asset
def inat_refined(inat_raw: list[dict]) -> list[dict]:
    return refine_observations(inat_raw)

@asset
def interactions(inat_refined: list[dict]):
    return to_interactions(inat_refined)

@asset
def load_dbs(context: AssetExecutionContext, interactions):
    cfg = load_config()
    run_id = context.run_id
    log_run(cfg.pg_dsn, run_id, "RUNNING", {"stage": "load", "interaction_count": len(interactions)})

    load_to_neo4j(cfg.neo4j_uri, cfg.neo4j_user, cfg.neo4j_pass, interactions)

    log_run(cfg.pg_dsn, run_id, "SUCCESS", {"stage": "done", "interaction_count": len(interactions)}, ended=True)
