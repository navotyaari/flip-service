import dataclasses
from datetime import timedelta
from typing import Callable

from temporalio.common import RetryPolicy


@dataclasses.dataclass(frozen=True)
class ServiceConfig:
    server_url: str
    endpoint: str
    is_partial_failure: Callable[[str], bool]
    retryable_status_codes: frozenset[int]
    non_retryable_status_codes: frozenset[int]
    max_batch_size: int
    start_to_close_timeout: timedelta
    retry_policy: RetryPolicy
