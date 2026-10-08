import httpx
import pytest_asyncio

import flip_service.activities as _activities_module
from tests.fixtures.flip_server import controlled_flip_server


@pytest_asyncio.fixture(autouse=True)
async def reset_http_client(monkeypatch):
    client = httpx.AsyncClient()
    monkeypatch.setattr(_activities_module, "_http_client", client)
    yield
    await client.aclose()


@pytest_asyncio.fixture
async def flip_server(mocker):
    async with controlled_flip_server() as base_url:
        mocker.patch("flip_service.activities.FLIP_SERVER_URL", base_url)
        yield base_url
