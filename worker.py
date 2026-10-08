import asyncio
import logging

import temporalio.client
import temporalio.worker

from flip_service.activities import flip_batch
from batch_processor.config import TASK_QUEUE, TEMPORAL_HOST
from batch_processor.log import setup_logging
from flip_service.workflow import Flip

interrupt_event = asyncio.Event()

ACTIVITIES = [flip_batch]
WORKFLOWS = [Flip]


async def main():
    setup_logging()

    client = await temporalio.client.Client.connect(TEMPORAL_HOST)
    async with temporalio.worker.Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=WORKFLOWS,
        activities=ACTIVITIES,
    ):
        logging.info("Worker started, ctrl+c to exit")
        await interrupt_event.wait()
        logging.info("Shutting down")


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        interrupt_event.set()
        loop.run_until_complete(loop.shutdown_asyncgens())
