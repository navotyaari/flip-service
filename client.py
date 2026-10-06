import asyncio
import random
import sys

import temporalio.client

from flip_service.workflow import Flip, Params


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
    if len(sys.argv) < 2:
        print("Usage: python client.py <string> [<string> ...]")
        sys.exit(1)

    flipped = asyncio.run(flip(sys.argv[1:]))

    print(" ".join(flipped))
