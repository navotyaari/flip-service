import dataclasses

import httpx
import pytest_asyncio

import flip_service.activities as _activities_module
from flip_service.service_config import SERVICE_CONFIG
from tests.fixtures.flip_server import controlled_flip_server


@pytest_asyncio.fixture(autouse=True)
async def reset_http_client(monkeypatch):
    client = httpx.AsyncClient(timeout=SERVICE_CONFIG.http_timeout.total_seconds())
    monkeypatch.setattr(_activities_module, "_http_client", client)
    yield
    await client.aclose()


@pytest_asyncio.fixture
async def flip_server(mocker):
    async with controlled_flip_server() as base_url:
        mocker.patch(
            "flip_service.activities.SERVICE_CONFIG",
            dataclasses.replace(SERVICE_CONFIG, server_url=base_url),
        )
        yield base_url
