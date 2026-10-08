import asyncio
import logging

import pytest
import temporalio.client

from client import flip
from flip_service.workflow import Flip, Result


@pytest.fixture
def mock_workflow_handle(mocker):
    handle = mocker.AsyncMock()
    handle.query.return_value = 0

    async def result_after_yield():
        await asyncio.sleep(0)
        return Result(strings=["olleh", "dlrow"])

    handle.result.side_effect = result_after_yield
    return handle


@pytest.fixture
def mock_temporal_client(mocker, mock_workflow_handle):
    temporal_client = mocker.AsyncMock()
    temporal_client.start_workflow.return_value = mock_workflow_handle
    mocker.patch("temporalio.client.Client.connect", return_value=temporal_client)
    mocker.patch("client.QUERY_POLL_INTERVAL", 0)
    return temporal_client


@pytest.fixture
def mock_failing_workflow_handle(mocker):
    handle = mocker.AsyncMock()
    handle.query.return_value = 0
    handle.result.side_effect = temporalio.client.WorkflowFailureError(
        cause=RuntimeError("workflow failed")
    )
    return handle


@pytest.fixture
def mock_temporal_client_failing(mocker, mock_failing_workflow_handle):
    temporal_client = mocker.AsyncMock()
    temporal_client.start_workflow.return_value = mock_failing_workflow_handle
    mocker.patch("temporalio.client.Client.connect", return_value=temporal_client)
    mocker.patch("client.QUERY_POLL_INTERVAL", 0)
    return temporal_client


class TestQueryLoop:
    @pytest.mark.asyncio
    async def test_queries_strings_flipped_count(self, mock_temporal_client, mock_workflow_handle):
        await flip(["hello", "world"])
        queried = [call.args[0] for call in mock_workflow_handle.query.call_args_list]
        assert Flip.get_strings_flipped_count in queried

    @pytest.mark.asyncio
    async def test_queries_http_200_count(self, mock_temporal_client, mock_workflow_handle):
        await flip(["hello", "world"])
        queried = [call.args[0] for call in mock_workflow_handle.query.call_args_list]
        assert Flip.get_http_200_count in queried

    @pytest.mark.asyncio
    async def test_poll_task_cancelled_after_completion(self, mock_temporal_client):
        await flip(["hello"])
        await asyncio.sleep(0)
        pending = [t for t in asyncio.all_tasks() if t != asyncio.current_task()]
        assert not pending

    @pytest.mark.asyncio
    async def test_execute_workflow_not_called(self, mock_temporal_client):
        await flip(["hello"])
        assert not mock_temporal_client.execute_workflow.called


class TestWorkflowFailure:
    @pytest.mark.asyncio
    async def test_raises_on_workflow_failure(self, mock_temporal_client_failing):
        with pytest.raises(temporalio.client.WorkflowFailureError):
            await flip(["hello"])


class TestOutput:
    @pytest.mark.asyncio
    async def test_result_printed_to_stdout(self, mock_temporal_client, capsys):
        await flip(["hello"])
        assert capsys.readouterr().out

    @pytest.mark.asyncio
    async def test_final_result_printed_to_stdout(self, mock_temporal_client, capsys):
        await flip(["hello", "world"])
        output = capsys.readouterr().out
        assert "olleh" in output
        assert "dlrow" in output

    @pytest.mark.asyncio
    async def test_progress_logged(self, mock_temporal_client, caplog):
        with caplog.at_level(logging.INFO):
            await flip(["hello"])
        assert any("flipped" in record.message for record in caplog.records)
