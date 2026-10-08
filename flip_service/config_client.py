import os

from flip_service.config_worker import TASK_QUEUE

TEMPORAL_HOST = os.getenv("TEMPORAL_HOST", "localhost:7233")
QUERY_POLL_INTERVAL = 2
