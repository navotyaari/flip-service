from datetime import timedelta

from temporalio.common import RetryPolicy

from flip_service.config_shared import TASK_QUEUE, TEMPORAL_HOST

FLIP_SERVER_PROCESSING_TIME = timedelta(seconds=5)
FLIP_BATCH_START_TO_CLOSE_TIMEOUT = FLIP_SERVER_PROCESSING_TIME * 6

FLIP_BATCH_RETRY_POLICY = RetryPolicy(
    maximum_attempts=10,
    initial_interval=timedelta(seconds=1),
    backoff_coefficient=2.0,
    non_retryable_error_types=["NonRetryableFlipError"],
)
