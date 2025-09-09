import os
import sys

import pytest
from fastapi.testclient import TestClient

# Add the project root to Python path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app

# Use TestClient for testing (no server needed)

client = TestClient(app)


def test_shorten_and_redirect():
    # create short

    resp = client.post("/shorten", json={"url": "https://example.com", "ttl_sec": 30})
    assert resp.status_code == 200
    data = resp.json()
    code = data["code"]

    # redirect

    resp2 = client.get(f"/{code}", follow_redirects=False)
    assert resp2.status_code in (302, 307)
    assert resp2.headers["location"] == "https://example.com/"

    # stats

    resp3 = client.get(f"/stats/{code}")
    assert resp3.status_code == 200
    stats = resp3.json()
    assert stats["clicks"] >= 1
    assert stats["ttl_remaining"] != -2  # -2 would mean missing


def test_top():
    # ensure at least one short link exists and gets clicked

    resp = client.post("/shorten", json={"url": "https://python.org"})
    assert resp.status_code == 200
    data = resp.json()
    code = data["code"]

    # visit the link to increment clicks and add to popular list

    client.get(f"/{code}", follow_redirects=False)

    # now check top

    resp = client.get("/top?limit=5")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
