import asyncio
import logging

import temporalio.client
import temporalio.worker
import temporalio.workflow

from flip_service.activities import flip_batch
from flip_service.config_worker import TEMPORAL_HOST
from flip_service.log import setup_logging
from flip_service.workflow import Flip

interrupt_event = asyncio.Event()

ACTIVITIES = [flip_batch]
WORKFLOWS = [Flip]


async def main():
    setup_logging()

    # Start client
    client = await temporalio.client.Client.connect(TEMPORAL_HOST)
    if not ACTIVITIES:
        logging.warning("No activities specified, worker will not be able to execute any non-workflow tasks")
    # Run a worker for the workflow
    async with temporalio.worker.Worker(
        client,
        task_queue="default",
        workflows=WORKFLOWS,
        activities=ACTIVITIES,
    ):
        # Wait until interrupted
        print("Worker started, ctrl+c to exit")
        await interrupt_event.wait()
        print("Shutting down")


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        interrupt_event.set()
        loop.run_until_complete(loop.shutdown_asyncgens())
