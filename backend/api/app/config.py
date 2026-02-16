import os

# Postgres
PG_DSN = os.getenv("PG_DSN", "postgresql://wew:wewpass@localhost:5432/wew")

# Neo4j
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASS = os.getenv("NEO4J_PASS", "neo4jpass")

# Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# CORS
ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")]

# Cache
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "300"))
