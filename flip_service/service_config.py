import http
import os
from datetime import timedelta

from temporalio.common import RetryPolicy

from batch_processor.service_config import ServiceConfig
from flip_service.errors import NonRetryableFlipError


_FLIP_SERVER_PROCESSING_TIME = timedelta(seconds=5)

SERVICE_CONFIG = ServiceConfig(
    server_url=os.getenv("FLIP_SERVER_URL", "http://127.0.0.1:8000"),
    endpoint="/flip",
    is_partial_failure=lambda r: r == "-",
    retryable_status_codes=frozenset({http.HTTPStatus.INTERNAL_SERVER_ERROR}),
    non_retryable_status_codes=frozenset({http.HTTPStatus.BAD_REQUEST}),
    max_batch_size=10,
    start_to_close_timeout=_FLIP_SERVER_PROCESSING_TIME * 6,
    retry_policy=RetryPolicy(
        maximum_attempts=10,
        initial_interval=timedelta(seconds=1),
        backoff_coefficient=2.0,
        non_retryable_error_types=[NonRetryableFlipError.__name__],
    ),
)
