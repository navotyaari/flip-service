import dataclasses

import pytest

from flip_service.activities import FlipBatch, FlipBatchResult, RetryableFlipError, flip_batch
from flip_service.service_config import SERVICE_CONFIG
from tests.fixtures.flip_server import controlled_flip_server


class TestHappyPath:
    @pytest.mark.asyncio
    async def test_flipped_strings_returned(self, flip_server):
        result = await flip_batch(FlipBatch(strings=["hello", "world"]))
        assert result == FlipBatchResult(strings=["olleh", "dlrow"])


class TestHttp500:
    @pytest.mark.asyncio
    async def test_raises_retryable_error(self, mocker):
        async with controlled_flip_server(always_500=True) as base_url:
            mocker.patch(
                "flip_service.activities.SERVICE_CONFIG",
                dataclasses.replace(SERVICE_CONFIG, server_url=base_url),
            )
            with pytest.raises(RetryableFlipError):
                await flip_batch(FlipBatch(strings=["hello"]))


class TestSentinelPassthrough:
    @pytest.mark.asyncio
    async def test_sentinel_returned_at_position(self, mocker):
        def fail_world(s: str) -> str:
            return "-" if s == "world" else s[::-1]

        async with controlled_flip_server(flip_string=fail_world) as base_url:
            mocker.patch(
                "flip_service.activities.SERVICE_CONFIG",
                dataclasses.replace(SERVICE_CONFIG, server_url=base_url),
            )
            result = await flip_batch(FlipBatch(strings=["hello", "world"]))

        assert result == FlipBatchResult(strings=["olleh", "-"])
