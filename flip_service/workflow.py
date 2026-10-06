import dataclasses

import temporalio.workflow

from flip_service.activities import MAX_BATCH_SIZE, FlipBatch, flip_batch
from flip_service.config_worker import FLIP_BATCH_RETRY_POLICY, FLIP_BATCH_START_TO_CLOSE_TIMEOUT


@dataclasses.dataclass
class Params:
    strings: list[str]


@dataclasses.dataclass
class Result:
    strings: list[str]


@temporalio.workflow.defn(name="Flip", sandboxed=False)
class Flip:
    def __init__(self) -> None:
        self._strings_flipped_count: int = 0
        self._http_200_count: int = 0

    @temporalio.workflow.run
    async def run(self, params: Params) -> Result:
        results: list[str | None] = [None] * len(params.strings)
        pending: list[tuple[int, str]] = list(enumerate(params.strings))

        while pending:
            batch = pending[:MAX_BATCH_SIZE]
            batch_result = await temporalio.workflow.execute_activity(
                flip_batch,
                FlipBatch(strings=[s for _, s in batch]),
                start_to_close_timeout=FLIP_BATCH_START_TO_CLOSE_TIMEOUT,
                retry_policy=FLIP_BATCH_RETRY_POLICY,
            )

            self._http_200_count += len(batch_result.strings)

            still_pending: list[tuple[int, str]] = []
            for (original_index, original_string), flipped in zip(batch, batch_result.strings):
                if flipped != "-":
                    results[original_index] = flipped
                    self._strings_flipped_count += 1
                else:
                    still_pending.append((original_index, original_string))

            pending = pending[MAX_BATCH_SIZE:] + still_pending

        return Result(strings=results)

    @temporalio.workflow.query
    def get_strings_flipped_count(self) -> int:
        return self._strings_flipped_count

    @temporalio.workflow.query
    def get_http_200_count(self) -> int:
        return self._http_200_count
