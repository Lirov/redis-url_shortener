import time
import string
import secrets
from typing import Optional, Tuple
import redis
from .config import settings

_pool = redis.ConnectionPool.from_url(str(settings.REDIS_URL), decode_responses=True)
r = redis.Redis(connection_pool=_pool)

ALPHABET = string.ascii_letters + string.digits

def gen_code(n: int) -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(n))

def store_url(original: str, ttl_sec: Optional[int] = None, code: Optional[str] = None) -> str:
    code = code or gen_code(settings.DEFAULT_CODE_LENGTH)
    key_url = f"url:{code}"
    key_meta = f"meta:{code}"
    key_clicks = f"clicks:{code}"

    # avoid accidental overwrite—regenerate if exists
    if r.exists(key_url):
        return store_url(original, ttl_sec, None)

    p = r.pipeline()
    p.set(key_url, original)
    p.hset(key_meta, mapping={"created_at": int(time.time()), "ttl_sec": ttl_sec or 0})
    p.setnx(key_clicks, 0)
    if ttl_sec:
        p.expire(key_url, ttl_sec)
        p.expire(key_meta, ttl_sec)
        p.expire(key_clicks, ttl_sec)
    p.execute()
    return code

def fetch_url(code: str) -> Optional[str]:
    return r.get(f"url:{code}")

def increment_clicks(code: str) -> int:
    new_val = r.incr(f"clicks:{code}")
    # reflect new score into sorted set
    r.zadd("links:popular", {code: new_val})
    return new_val

def get_stats(code: str) -> Optional[dict]:
    key_url = f"url:{code}"
    key_meta = f"meta:{code}"
    key_clicks = f"clicks:{code}"

    if not r.exists(key_url):
        return None

    ttl = r.ttl(key_url)  # -1 = no TTL, -2 = not exist
    clicks = int(r.get(key_clicks) or 0)
    meta = r.hgetall(key_meta)
    return {
        "code": code,
        "original": r.get(key_url),
        "clicks": clicks,
        "ttl_remaining": ttl if ttl is not None else -1,
        "created_at": int(meta.get("created_at", 0)),
        "ttl_sec": int(meta.get("ttl_sec", 0)),
    }

def get_top(limit: int = 10) -> list[Tuple[str, int]]:
    # highest scores first
    items = r.zrevrange("links:popular", 0, limit - 1, withscores=True)
    return [(code, int(score)) for code, score in items]
