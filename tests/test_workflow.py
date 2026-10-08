import uuid

import pytest
from temporalio import activity
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

from flip_service.activities import FlipBatch, FlipBatchResult
from flip_service.service_config import SERVICE_CONFIG
from flip_service.workflow import Flip, Params, Result


def workflow_id() -> str:
    return f"test-{uuid.uuid4()}"


def simple_mock():
    @activity.defn(name="flip_batch")
    async def mock(batch: FlipBatch) -> FlipBatchResult:
        return FlipBatchResult(strings=[s[::-1] for s in batch.strings])

    return mock


def sequential_mock(responses: list[list[str]]):
    iterator = iter(responses)

    @activity.defn(name="flip_batch")
    async def mock(batch: FlipBatch) -> FlipBatchResult:
        return FlipBatchResult(strings=next(iterator))

    return mock


def counting_mock():
    call_batches: list[list[str]] = []

    @activity.defn(name="flip_batch")
    async def mock(batch: FlipBatch) -> FlipBatchResult:
        call_batches.append(list(batch.strings))
        return FlipBatchResult(strings=[s[::-1] for s in batch.strings])

    return mock, call_batches


class TestHappyPath:
    @pytest.mark.asyncio
    async def test_all_strings_flipped(self):
        async with await WorkflowEnvironment.start_time_skipping() as env:
            async with Worker(
                env.client, task_queue="test", workflows=[Flip], activities=[simple_mock()]
            ):
                result = await env.client.execute_workflow(
                    Flip.run,
                    Params(strings=["hello", "world"]),
                    id=workflow_id(),
                    task_queue="test",
                )
        assert result == Result(strings=["olleh", "dlrow"])


class TestPartialFailure:
    @pytest.mark.asyncio
    async def test_dash_strings_are_retried_until_resolved(self):
        mock = sequential_mock([
            ["olleh", "-"],  # hello flips, world fails
            ["dlrow"],       # world retried and flips
        ])
        async with await WorkflowEnvironment.start_time_skipping() as env:
            async with Worker(
                env.client, task_queue="test", workflows=[Flip], activities=[mock]
            ):
                result = await env.client.execute_workflow(
                    Flip.run,
                    Params(strings=["hello", "world"]),
                    id=workflow_id(),
                    task_queue="test",
                )
        assert result == Result(strings=["olleh", "dlrow"])


class TestBatching:
    @pytest.mark.asyncio
    async def test_input_exceeding_batch_size_splits_into_multiple_calls(self):
        mock, call_batches = counting_mock()
        strings = [chr(ord("a") + i) * 3 for i in range(SERVICE_CONFIG.max_batch_size + 1)]

        async with await WorkflowEnvironment.start_time_skipping() as env:
            async with Worker(
                env.client, task_queue="test", workflows=[Flip], activities=[mock]
            ):
                await env.client.execute_workflow(
                    Flip.run,
                    Params(strings=strings),
                    id=workflow_id(),
                    task_queue="test",
                )

        assert len(call_batches) >= 2
        assert all(len(batch) <= SERVICE_CONFIG.max_batch_size for batch in call_batches)


class TestQueries:
    @pytest.mark.asyncio
    async def test_strings_flipped_count_after_completion(self):
        async with await WorkflowEnvironment.start_time_skipping() as env:
            async with Worker(
                env.client, task_queue="test", workflows=[Flip], activities=[simple_mock()]
            ):
                handle = await env.client.start_workflow(
                    Flip.run,
                    Params(strings=["hello", "world", "foo"]),
                    id=workflow_id(),
                    task_queue="test",
                )
                await handle.result()
                count = await handle.query(Flip.get_strings_flipped_count)
        assert count == 3

    @pytest.mark.asyncio
    async def test_http_200_count_after_completion(self):
        async with await WorkflowEnvironment.start_time_skipping() as env:
            async with Worker(
                env.client, task_queue="test", workflows=[Flip], activities=[simple_mock()]
            ):
                handle = await env.client.start_workflow(
                    Flip.run,
                    Params(strings=["hello", "world", "foo"]),
                    id=workflow_id(),
                    task_queue="test",
                )
                await handle.result()
                count = await handle.query(Flip.get_http_200_count)
        assert count == 1


class TestCounterDivergence:
    @pytest.mark.asyncio
    async def test_http_200_count_exceeds_flipped_count_after_partial_failure(self):
        # world fails twice: 3 calls total, 2 strings flipped → http_200_count (3) > strings_flipped_count (2)
        mock = sequential_mock([
            ["olleh", "-"],  # call 1: hello flips, world fails
            ["-"],            # call 2: world fails again
            ["dlrow"],                             # call 3: world finally flips
        ])
        async with await WorkflowEnvironment.start_time_skipping() as env:
            async with Worker(
                env.client, task_queue="test", workflows=[Flip], activities=[mock]
            ):
                handle = await env.client.start_workflow(
                    Flip.run,
                    Params(strings=["hello", "world"]),
                    id=workflow_id(),
                    task_queue="test",
                )
                await handle.result()
                flipped_count = await handle.query(Flip.get_strings_flipped_count)
                http_200_count = await handle.query(Flip.get_http_200_count)

        assert http_200_count > flipped_count


class TestOutputOrder:
    @pytest.mark.asyncio
    async def test_result_index_matches_input_index_after_retry(self):
        mock = sequential_mock([
            ["olleh", "-", "oof"],  # world at index 1 fails
            ["dlrow"],              # world retried and flipped
        ])
        async with await WorkflowEnvironment.start_time_skipping() as env:
            async with Worker(
                env.client, task_queue="test", workflows=[Flip], activities=[mock]
            ):
                result = await env.client.execute_workflow(
                    Flip.run,
                    Params(strings=["hello", "world", "foo"]),
                    id=workflow_id(),
                    task_queue="test",
                )

        assert result.strings[0] == "olleh"  # index 0: hello
        assert result.strings[1] == "dlrow"  # index 1: world (was retried)
        assert result.strings[2] == "oof"    # index 2: foo
