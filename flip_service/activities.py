import dataclasses
import http

import httpx
import temporalio.activity
import temporalio.exceptions

from flip_service.config import FLIP_SERVER_URL

MAX_BATCH_SIZE = 10


@dataclasses.dataclass
class FlipBatch:
    strings: list[str]


@dataclasses.dataclass
class FlipBatchResult:
    strings: list[str]


class RetryableFlipError(Exception):
    pass


class NonRetryableFlipError(temporalio.exceptions.ApplicationError):
    def __init__(self, message: str):
        super().__init__(message, non_retryable=True)


@temporalio.activity.defn
async def flip_batch(batch: FlipBatch) -> FlipBatchResult:
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{FLIP_SERVER_URL}/flip", json=batch.strings)

    if response.status_code == http.HTTPStatus.INTERNAL_SERVER_ERROR:
        raise RetryableFlipError(response.text)
    if response.status_code == http.HTTPStatus.BAD_REQUEST:
        raise NonRetryableFlipError(response.text)

    return FlipBatchResult(strings=response.json())
