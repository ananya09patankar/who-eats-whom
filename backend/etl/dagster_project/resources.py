from dataclasses import dataclass
import os

@dataclass
class Config:
    pg_dsn: str
    neo4j_uri: str
    neo4j_user: str
    neo4j_pass: str

def load_config() -> Config:
    return Config(
        pg_dsn=os.environ["PG_DSN"],
        neo4j_uri=os.environ["NEO4J_URI"],
        neo4j_user=os.environ["NEO4J_USER"],
        neo4j_pass=os.environ["NEO4J_PASS"],
    )
