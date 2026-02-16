from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import ALLOWED_ORIGINS
from .db_pg import (
    get_etl_status,
    get_cache_version,
    get_prey_from_pg,
    get_predators_from_pg,
    get_diet_summary,
)
from .db_neo4j import get_prey, get_predators
from .cache import get_json, set_json

app = FastAPI(title="Who-Eats-Whom API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/api/v1/etl/status")
def etl_status():
    return get_etl_status()

@app.get("/api/v1/species/{taxon_id}/prey")
def species_prey(taxon_id: int, limit: int = 50):
    ver = get_cache_version()
    cache_key = f"v{ver}:prey:{taxon_id}:limit:{limit}"
    cached = get_json(cache_key)
    if cached is not None:
        return {"taxon_id": taxon_id, "prey": cached, "cached": True, "version": ver}

    prey = get_prey(taxon_id=taxon_id, limit=limit)
    set_json(cache_key, prey)
    return {"taxon_id": taxon_id, "prey": prey, "cached": False, "version": ver}

@app.get("/api/v1/species/{taxon_id}/predators")
def species_predators(taxon_id: int, limit: int = 50):
    ver = get_cache_version()
    cache_key = f"v{ver}:predators:{taxon_id}:limit:{limit}"
    cached = get_json(cache_key)
    if cached is not None:
        return {"taxon_id": taxon_id, "predators": cached, "cached": True, "version": ver}

    preds = get_predators(taxon_id=taxon_id, limit=limit)
    set_json(cache_key, preds)
    return {"taxon_id": taxon_id, "predators": preds, "cached": False, "version": ver}

@app.get("/")
def root():
    return {"service": "Who-Eats-Whom API", "ok": True}

@app.get("/api/v1/species/{taxon_id}/summary")
def species_summary(taxon_id: int, limit: int = 20):
    return get_diet_summary(predator_taxon_id=taxon_id, limit=limit)


@app.get("/api/v1/species/{taxon_id}/prey_pg")
def species_prey_pg(taxon_id: int, limit: int = 50):
    return get_prey_from_pg(predator_taxon_id=taxon_id, limit=limit)


@app.get("/api/v1/species/{taxon_id}/predators_pg")
def species_predators_pg(taxon_id: int, limit: int = 50):
    return get_predators_from_pg(prey_taxon_id=taxon_id, limit=limit)
