import asyncio
import logging
import random
import re
import sys

import temporalio.client

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
        target_host="localhost:7233",
    )

    flip_result = await client.execute_workflow(
        Flip.run,
        Params(strings=to_flip),
        id=f"flip-{random.randint(0, 100000)}",
        task_queue="default",
    )

    return flip_result.strings


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

    flipped = asyncio.run(flip(sys.argv[1:]))

    print(" ".join(flipped))
