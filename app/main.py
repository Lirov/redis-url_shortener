from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, HttpUrl
from typing import Optional
from .storage import store_url, fetch_url, increment_clicks, get_stats, get_top
from .config import settings

app = FastAPI(title="Redis URL Shortener")

class ShortenRequest(BaseModel):
    url: HttpUrl
    ttl_sec: Optional[int] = None
    custom_code: Optional[str] = None

class ShortenResponse(BaseModel):
    code: str
    short_url: str

@app.post("/shorten", response_model=ShortenResponse)
def shorten(payload: ShortenRequest):
    code = store_url(str(payload.url), payload.ttl_sec, payload.custom_code)
    return ShortenResponse(code=code, short_url=f"{settings.BASE_URL}/{code}")

@app.get("/{code}")
def redirect(code: str):
    original = fetch_url(code)
    if not original:
        raise HTTPException(status_code=404, detail="Code not found or expired")
    increment_clicks(code)
    return RedirectResponse(url=original, status_code=307)

@app.get("/stats/{code}")
def stats(code: str):
    s = get_stats(code)
    if not s:
        raise HTTPException(status_code=404, detail="Code not found or expired")
    return s

@app.get("/top")
def top(limit: int = 10):
    return [{"code": code, "clicks": clicks} for code, clicks in get_top(limit)]
