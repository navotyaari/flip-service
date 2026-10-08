import dataclasses
from typing import cast

import temporalio.workflow

with temporalio.workflow.unsafe.imports_passed_through():
    from flip_service.activities import FlipBatch, flip_batch
    from flip_service.service_config import SERVICE_CONFIG

from flip_service.config import FLIP_BATCH_RETRY_POLICY, FLIP_BATCH_START_TO_CLOSE_TIMEOUT


@dataclasses.dataclass
class Params:
    strings: list[str]


@dataclasses.dataclass
class Result:
    strings: list[str]


@temporalio.workflow.defn(name="Flip")
class Flip:
    def __init__(self) -> None:
        self._strings_flipped_count: int = 0
        self._http_200_count: int = 0

    @temporalio.workflow.run
    async def run(self, params: Params) -> Result:
        result_buffer: list[str | None] = [None] * len(params.strings)
        pending: list[tuple[int, str]] = list(enumerate(params.strings))

        while pending:
            batch = pending[:SERVICE_CONFIG.max_batch_size]
            batch_result = await temporalio.workflow.execute_activity(
                flip_batch,
                FlipBatch(strings=[s for _, s in batch]),
                start_to_close_timeout=FLIP_BATCH_START_TO_CLOSE_TIMEOUT,
                retry_policy=FLIP_BATCH_RETRY_POLICY,
            )

            self._http_200_count += 1

            still_pending: list[tuple[int, str]] = []
            for (original_index, original_string), flipped in zip(batch, batch_result.strings):
                if not SERVICE_CONFIG.is_partial_failure(flipped):
                    result_buffer[original_index] = flipped
                    self._strings_flipped_count += 1
                else:
                    still_pending.append((original_index, original_string))

            pending = pending[SERVICE_CONFIG.max_batch_size:] + still_pending

        return Result(strings=cast(list[str], result_buffer))

    @temporalio.workflow.query
    def get_strings_flipped_count(self) -> int:
        return self._strings_flipped_count

    @temporalio.workflow.query
    def get_http_200_count(self) -> int:
        return self._http_200_count
