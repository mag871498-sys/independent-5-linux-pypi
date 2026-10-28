"""Навантажувальна перевірка JSON-сервера."""

import os

from molotov import scenario

URL = os.environ.get("LOADTEST_URL", "http://127.0.0.1:8085/")


@scenario(weight=100)
async def json_ok(session):
    async with session.get(URL) as response:
        assert response.status == 200, f"HTTP {response.status}"
        body = await response.json()
        assert isinstance(body, dict) and body.get("status") == "ok", body
