import dataclasses
import http

import httpx
import temporalio.activity

from flip_service.errors import NonRetryableFlipError, RetryableFlipError
from flip_service.service_config import SERVICE_CONFIG

_http_client = httpx.AsyncClient()


@dataclasses.dataclass
class FlipBatch:
    strings: list[str]


@dataclasses.dataclass
class FlipBatchResult:
    strings: list[str]


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
