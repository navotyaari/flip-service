import os
from datetime import timedelta

from temporalio.common import RetryPolicy

FLIP_SERVER_URL = os.getenv("FLIP_SERVER_URL", "http://127.0.0.1:8000")
FLIP_SERVER_PROCESSING_TIME = timedelta(seconds=5)
FLIP_BATCH_START_TO_CLOSE_TIMEOUT = FLIP_SERVER_PROCESSING_TIME * 6

FLIP_BATCH_RETRY_POLICY = RetryPolicy(
    maximum_attempts=10,
    initial_interval=timedelta(seconds=1),
    backoff_coefficient=2.0,
    non_retryable_error_types=["NonRetryableFlipError"],
)
