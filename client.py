import asyncio
import logging
import re
import uuid
import sys

import temporalio.client

from flip_service.config_client import QUERY_POLL_INTERVAL, TEMPORAL_HOST
from flip_service.log import setup_logging
from flip_service.workflow import Flip, Params


def validate_inputs(strings: list[str]) -> None:
    if not strings:
        raise ValueError("at least one string is required")
    invalid = [s for s in strings if not re.fullmatch(r"[a-z]+", s)]
    if invalid:
        raise ValueError(f"invalid strings (only lowercase a-z allowed): {', '.join(invalid)}")


async def flip(to_flip: list[str]) -> list[str]:
    client = await temporalio.client.Client.connect(
        target_host=TEMPORAL_HOST,
    )

    handle = await client.start_workflow(
        Flip.run,
        Params(strings=to_flip),
        id=f"flip-{uuid.uuid4()}",
        task_queue="default",
    )

    async def poll_progress():
        while True:
            try:
                flipped_count = await handle.query(Flip.get_strings_flipped_count)
                http_200_count = await handle.query(Flip.get_http_200_count)
                print(f"Progress: {flipped_count} strings flipped, {http_200_count} HTTP 200s")
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logging.warning(f"Progress query failed: {exc}")
            await asyncio.sleep(QUERY_POLL_INTERVAL)

    poll_task = asyncio.create_task(poll_progress())
    try:
        result = await handle.result()
    finally:
        poll_task.cancel()
        try:
            await poll_task
        except asyncio.CancelledError:
            pass

    print(" ".join(result.strings))
    return result.strings


if __name__ == "__main__":
    setup_logging()

    if len(sys.argv) < 2:
        logging.error("Usage: python client.py <string> [<string> ...]")
        sys.exit(1)

    try:
        validate_inputs(sys.argv[1:])
    except ValueError as exc:
        logging.error(exc)
        sys.exit(1)

    try:
        asyncio.run(flip(sys.argv[1:]))
    except temporalio.client.WorkflowFailureError as exc:
        logging.error(exc)
        sys.exit(1)
