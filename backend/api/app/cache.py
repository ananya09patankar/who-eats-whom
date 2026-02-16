import json
import redis
from .config import REDIS_URL, CACHE_TTL_SECONDS

_r = redis.Redis.from_url(REDIS_URL, decode_responses=True)

def get_json(key: str):
    v = _r.get(key)
    return json.loads(v) if v else None

def set_json(key: str, obj, ttl: int = CACHE_TTL_SECONDS):
    _r.setex(key, ttl, json.dumps(obj))
