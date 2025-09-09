import secrets
import string
import time
from typing import Optional, Tuple

import redis

from .config import settings

# Try to connect to Redis, fall back to mock if not available

try:
    _pool = redis.ConnectionPool.from_url(
        str(settings.REDIS_URL), decode_responses=True
    )
    r = redis.Redis(connection_pool=_pool)
    # Test connection

    r.ping()
    print("✅ Connected to Redis")
except redis.exceptions.ConnectionError:
    print("⚠️  Redis not available, using in-memory storage for development")
    # Mock Redis implementation for development

    class MockRedis:
        def __init__(self):
            self.data = {}
            self.expires = {}
            self.hashes = {}
            self.sorted_sets = {}

        def exists(self, key):
            return key in self.data

        def set(self, key, value):
            self.data[key] = value

        def get(self, key):
            return self.data.get(key)

        def hset(self, key, mapping=None, **kwargs):
            if key not in self.hashes:
                self.hashes[key] = {}
            if mapping:
                self.hashes[key].update(mapping)
            self.hashes[key].update(kwargs)

        def hgetall(self, key):
            return self.hashes.get(key, {})

        def setnx(self, key, value):
            if key not in self.data:
                self.data[key] = value
                return True
            return False

        def expire(self, key, seconds):
            self.expires[key] = time.time() + seconds

        def ttl(self, key):
            if key in self.expires:
                remaining = self.expires[key] - time.time()
                return int(remaining) if remaining > 0 else -2
            return -1

        def incr(self, key):
            current = int(self.data.get(key, 0))
            new_val = current + 1
            self.data[key] = str(new_val)
            return new_val

        def zadd(self, key, mapping):
            if key not in self.sorted_sets:
                self.sorted_sets[key] = {}
            self.sorted_sets[key].update(mapping)

        def zrevrange(self, key, start, end, withscores=False):
            if key not in self.sorted_sets:
                return []
            items = sorted(
                self.sorted_sets[key].items(), key=lambda x: x[1], reverse=True
            )
            if end == -1:
                # -1 means get all items from start to end

                selected_items = items[start:]
            else:
                selected_items = items[start : end + 1]
            if withscores:
                return selected_items
            return [item[0] for item in selected_items]

        def pipeline(self):
            return MockPipeline(self)

        def ping(self):
            return True

    class MockPipeline:
        def __init__(self, redis):
            self.redis = redis
            self.commands = []

        def set(self, key, value):
            self.commands.append(("set", key, value))
            return self

        def hset(self, key, mapping=None, **kwargs):
            self.commands.append(("hset", key, mapping, kwargs))
            return self

        def setnx(self, key, value):
            self.commands.append(("setnx", key, value))
            return self

        def expire(self, key, seconds):
            self.commands.append(("expire", key, seconds))
            return self

        def execute(self):
            for cmd in self.commands:
                if cmd[0] == "set":
                    self.redis.set(cmd[1], cmd[2])
                elif cmd[0] == "hset":
                    self.redis.hset(cmd[1], mapping=cmd[2], **cmd[3])
                elif cmd[0] == "setnx":
                    self.redis.setnx(cmd[1], cmd[2])
                elif cmd[0] == "expire":
                    self.redis.expire(cmd[1], cmd[2])
            self.commands = []

    r = MockRedis()
ALPHABET = string.ascii_letters + string.digits


def gen_code(n: int) -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(n))


def store_url(
    original: str, ttl_sec: Optional[int] = None, code: Optional[str] = None
) -> str:
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
