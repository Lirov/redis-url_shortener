import os
import httpx
import pytest
from uuid import uuid4

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

@pytest.mark.asyncio
async def test_register_login_and_shortening():
    username = f"user_{uuid4().hex[:8]}"
    password = "P@ssw0rd!"

    async with httpx.AsyncClient(base_url=BASE_URL) as c:
        r = await c.post("/auth/register", json={"username": username, "password": password})
        assert r.status_code == 200

        r = await c.post("/auth/login", json={"username": username, "password": password})
        assert r.status_code == 200
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        r = await c.post("/shorten", headers=headers, json={"url": "https://example.com"})
        assert r.status_code == 200
        code = r.json()["code"]

        # public redirect still works without token
        r = await c.get(f"/{code}", follow_redirects=False)
        assert r.status_code in (302, 307)
