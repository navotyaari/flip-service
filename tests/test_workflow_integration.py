import uuid
from collections import defaultdict

import pytest
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

from flip_service.activities import flip_batch
from flip_service.config_worker import MAX_BATCH_SIZE, PARTIAL_FAILURE_SENTINEL
from flip_service.workflow import Flip, Params, Result
from tests.fixtures.flip_server import controlled_flip_server


def workflow_id() -> str:
    return f"test-{uuid.uuid4()}"


@pytest.mark.integration
class TestHappyPath:
    @pytest.mark.asyncio
    async def test_all_strings_flipped_in_order(self, flip_server):
        async with await WorkflowEnvironment.start_local() as env:
            async with Worker(env.client, task_queue="test", workflows=[Flip], activities=[flip_batch]):
                result = await env.client.execute_workflow(
                    Flip.run,
                    Params(strings=["hello", "world"]),
                    id=workflow_id(),
                    task_queue="test",
                )
        assert result == Result(strings=["olleh", "dlrow"])


@pytest.mark.integration
class TestPartialFailureAndRecovery:
    @pytest.mark.asyncio
    async def test_retried_strings_resolved(self, mocker):
        attempt_counts: defaultdict[str, int] = defaultdict(int)

        def fail_first_attempt(s: str) -> str:
            attempt_counts[s] += 1
            if attempt_counts[s] == 1 and s == "world":
                return PARTIAL_FAILURE_SENTINEL
            return s[::-1]

        async with controlled_flip_server(flip_string=fail_first_attempt) as base_url:
            mocker.patch("flip_service.activities.FLIP_SERVER_URL", base_url)
            async with await WorkflowEnvironment.start_local() as env:
                async with Worker(env.client, task_queue="test", workflows=[Flip], activities=[flip_batch]):
                    result = await env.client.execute_workflow(
                        Flip.run,
                        Params(strings=["hello", "world"]),
                        id=workflow_id(),
                        task_queue="test",
                    )

        assert result == Result(strings=["olleh", "dlrow"])


@pytest.mark.integration
class TestCounterAccuracy:
    @pytest.mark.asyncio
    async def test_counters_correct_after_partial_failure(self, mocker):
        attempt_counts: defaultdict[str, int] = defaultdict(int)

        def fail_first_attempt(s: str) -> str:
            attempt_counts[s] += 1
            if attempt_counts[s] == 1 and s == "world":
                return PARTIAL_FAILURE_SENTINEL
            return s[::-1]

        async with controlled_flip_server(flip_string=fail_first_attempt) as base_url:
            mocker.patch("flip_service.activities.FLIP_SERVER_URL", base_url)
            async with await WorkflowEnvironment.start_local() as env:
                async with Worker(env.client, task_queue="test", workflows=[Flip], activities=[flip_batch]):
                    handle = await env.client.start_workflow(
                        Flip.run,
                        Params(strings=["hello", "world", "foo"]),
                        id=workflow_id(),
                        task_queue="test",
                    )
                    await handle.result()
                    strings_flipped = await handle.query(Flip.get_strings_flipped_count)
                    http_200_count = await handle.query(Flip.get_http_200_count)

        assert strings_flipped == 3
        assert http_200_count == 4  # batch 1: 3 strings, retry batch: 1 string


@pytest.mark.integration
class TestOutputOrder:
    @pytest.mark.asyncio
    async def test_order_preserved_across_batches(self, flip_server):
        strings = [chr(ord("a") + i) * 3 for i in range(MAX_BATCH_SIZE + 1)]

        async with await WorkflowEnvironment.start_local() as env:
            async with Worker(env.client, task_queue="test", workflows=[Flip], activities=[flip_batch]):
                result = await env.client.execute_workflow(
                    Flip.run,
                    Params(strings=strings),
                    id=workflow_id(),
                    task_queue="test",
                )

        assert result.strings == [s[::-1] for s in strings]
