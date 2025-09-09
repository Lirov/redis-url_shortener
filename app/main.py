from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, HttpUrl
from typing import Optional
from .storage import store_url, fetch_url, increment_clicks, get_stats, get_top
from .config import settings
from .users import create_user, verify_user, user_exists
from .security import create_access_token, auth_required

app = FastAPI(title="Redis URL Shortener")


# ---------- Auth models ----------
class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@app.post("/auth/register")
def register(body: RegisterRequest):
    if user_exists(body.username):
        raise HTTPException(status_code=400, detail="Username already exists")
    ok = create_user(body.username, body.password)
    if not ok:
        raise HTTPException(status_code=500, detail="Unable to create user")
    return {"ok": True}


@app.post("/auth/login", response_model=TokenResponse)
def login(body: LoginRequest):
    if not verify_user(body.username, body.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(sub=body.username)
    return TokenResponse(access_token=token)


# ---------- URL shortener ----------
class ShortenRequest(BaseModel):
    url: HttpUrl
    ttl_sec: Optional[int] = None
    custom_code: Optional[str] = None


class ShortenResponse(BaseModel):
    code: str
    short_url: str


@app.post("/shorten", response_model=ShortenResponse)
def shorten(payload: ShortenRequest, _user: str = Depends(auth_required)):
    code = store_url(str(payload.url), payload.ttl_sec, payload.custom_code)
    return ShortenResponse(code=code, short_url=f"{settings.BASE_URL}/{code}")


# protect stats/top (optional; remove Depends to make public)
@app.get("/stats/{code}")
def stats(code: str, _user: str = Depends(auth_required)):
    s = get_stats(code)
    if not s:
        raise HTTPException(status_code=404, detail="Code not found or expired")
    return s


@app.get("/top")
def top(limit: int = 10, _user: str = Depends(auth_required)):
    return [{"code": code, "clicks": clicks} for code, clicks in get_top(limit)]


# keep redirect public (must be last to avoid conflicts)
@app.get("/{code}")
def redirect(code: str):
    original = fetch_url(code)
    if not original:
        raise HTTPException(status_code=404, detail="Code not found or expired")
    increment_clicks(code)
    return RedirectResponse(url=original, status_code=307)
