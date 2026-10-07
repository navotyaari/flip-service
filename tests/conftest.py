import pytest_asyncio

from tests.fixtures.flip_server import controlled_flip_server


@pytest_asyncio.fixture
async def flip_server(mocker):
    async with controlled_flip_server() as base_url:
        mocker.patch("flip_service.activities.FLIP_SERVER_URL", base_url)
        yield base_url
