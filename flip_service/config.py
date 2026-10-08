import os

TEMPORAL_HOST = os.getenv("TEMPORAL_HOST", "localhost:7233")
TASK_QUEUE = "default"
QUERY_POLL_INTERVAL = 2
