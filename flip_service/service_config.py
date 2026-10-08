import dataclasses
import http
import os
from typing import Callable


@dataclasses.dataclass(frozen=True)
class ServiceConfig:
    server_url: str
    endpoint: str
    is_partial_failure: Callable[[str], bool]
    retryable_status_codes: frozenset[int]
    non_retryable_status_codes: frozenset[int]
    max_batch_size: int


SERVICE_CONFIG = ServiceConfig(
    server_url=os.getenv("FLIP_SERVER_URL", "http://127.0.0.1:8000"),
    endpoint="/flip",
    is_partial_failure=lambda r: r == "-",
    retryable_status_codes=frozenset({http.HTTPStatus.INTERNAL_SERVER_ERROR}),
    non_retryable_status_codes=frozenset({http.HTTPStatus.BAD_REQUEST}),
    max_batch_size=10,
)
