from typing import Optional
from passlib.context import CryptContext
import redis
from .config import settings

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
_pool = redis.ConnectionPool.from_url(str(settings.REDIS_URL), decode_responses=True)
r = redis.Redis(connection_pool=_pool)

def _user_key(username: str) -> str:
    return f"user:{username}"

def create_user(username: str, password: str) -> bool:
    key = _user_key(username)
    if r.exists(key):
        return False
    r.hset(key, mapping={"password_hash": pwd_ctx.hash(password)})
    return True

def verify_user(username: str, password: str) -> bool:
    key = _user_key(username)
    if not r.exists(key):
        return False
    ph = r.hget(key, "password_hash")
    return pwd_ctx.verify(password, ph)

def user_exists(username: str) -> bool:
    return r.exists(_user_key(username)) == 1
