from neo4j import GraphDatabase
from .transform import Interaction

def load_to_neo4j(uri: str, user: str, password: str, interactions: list[Interaction]) -> None:
    driver = GraphDatabase.driver(uri, auth=(user, password))
    cypher = '''
    MERGE (pred:Species {taxon_id: $pred})
    MERGE (prey:Species {taxon_id: $prey})
    MERGE (pred)-[r:EATS]->(prey)
    ON CREATE SET r.count = 1, r.last_obs_id = $obs
    ON MATCH SET r.count = r.count + 1, r.last_obs_id = $obs
    '''
    with driver.session() as session:
        for it in interactions:
            session.run(cypher, pred=it.predator_taxon_id, prey=it.prey_taxon_id, obs=it.evidence_obs_id)
    driver.close()
