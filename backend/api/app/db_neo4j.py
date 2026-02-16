from neo4j import GraphDatabase
from .config import NEO4J_URI, NEO4J_USER, NEO4J_PASS

def _driver():
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))

def get_prey(taxon_id: int, limit: int = 50) -> list[dict]:
    """
    Assumes graph model:
      (:Species {taxon_id})-[:EATS {count?}]->(:Species {taxon_id})
    Returns prey list for a predator taxon_id.
    """
    q = """
    MATCH (pred:Species {taxon_id: $taxon_id})-[r:EATS]->(prey:Species)
    RETURN prey.taxon_id AS taxon_id,
        coalesce(prey.scientific_name, prey.common_name, prey.name, "") AS name,
        coalesce(r.count, 1) AS count
    ORDER BY count DESC
    LIMIT $limit

    """
    with _driver() as d:
        with d.session() as s:
            res = s.run(q, taxon_id=taxon_id, limit=limit)
            return [dict(r) for r in res]

def get_predators(taxon_id: int, limit: int = 50) -> list[dict]:
    """
    Returns predator list for a prey taxon_id.
    """
    q = """
    MATCH (pred:Species)-[r:EATS]->(prey:Species {taxon_id: $taxon_id})
    RETURN pred.taxon_id AS taxon_id,
        coalesce(pred.scientific_name, pred.common_name, pred.name, "") AS name,
        coalesce(r.count, 1) AS count
    ORDER BY count DESC
    LIMIT $limit

    """
    with _driver() as d:
        with d.session() as s:
            res = s.run(q, taxon_id=taxon_id, limit=limit)
            return [dict(r) for r in res]
