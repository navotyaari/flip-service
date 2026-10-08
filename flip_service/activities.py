import dataclasses
import http

import httpx
import temporalio.activity
import temporalio.exceptions

from flip_service.service_config import SERVICE_CONFIG

_http_client = httpx.AsyncClient()


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
    response = await _http_client.post(
        f"{SERVICE_CONFIG.server_url}{SERVICE_CONFIG.endpoint}",
        json=batch.strings,
    )

    if response.status_code in SERVICE_CONFIG.retryable_status_codes:
        raise RetryableFlipError(response.text)
    if response.status_code in SERVICE_CONFIG.non_retryable_status_codes:
        raise NonRetryableFlipError(response.text)
    if response.status_code != http.HTTPStatus.OK:
        raise RetryableFlipError(f"unexpected status {response.status_code.value}: {response.text}")

    return FlipBatchResult(strings=response.json())
