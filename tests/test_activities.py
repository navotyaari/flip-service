import http

import pytest
from pytest_mock import MockerFixture

from flip_service.activities import (
    FlipBatch,
    FlipBatchResult,
    NonRetryableFlipError,
    RetryableFlipError,
    flip_batch,
)
from flip_service.config import FLIP_BATCH_RETRY_POLICY
from flip_service.service_config import SERVICE_CONFIG


def make_response(mocker: MockerFixture, status_code: http.HTTPStatus, body: list[str] | None = None):
    response = mocker.MagicMock(status_code=status_code)
    if body is not None:
        response.json.return_value = body
    return response


@pytest.fixture
def mock_post(mocker: MockerFixture):
    return mocker.patch("flip_service.activities._http_client.post")


class TestRetryPolicy:
    def test_non_retryable_error_is_listed(self):
        assert "NonRetryableFlipError" in FLIP_BATCH_RETRY_POLICY.non_retryable_error_types

    def test_retryable_error_is_not_listed(self):
        assert "RetryableFlipError" not in FLIP_BATCH_RETRY_POLICY.non_retryable_error_types

    def test_max_attempts_is_not_unlimited(self):
        assert FLIP_BATCH_RETRY_POLICY.maximum_attempts > 0

    def test_initial_interval_is_set(self):
        assert FLIP_BATCH_RETRY_POLICY.initial_interval is not None

    def test_backoff_coefficient_is_greater_than_one(self):
        assert FLIP_BATCH_RETRY_POLICY.backoff_coefficient > 1.0


class TestHappyPath:
    @pytest.mark.asyncio
    async def test_returns_flipped_strings(self, mock_post, mocker):
        mock_post.return_value = make_response(mocker, http.HTTPStatus.OK, ["olleh", "dlrow"])
        result = await flip_batch(FlipBatch(strings=["hello", "world"]))
        assert result == FlipBatchResult(strings=["olleh", "dlrow"])

    @pytest.mark.asyncio
    async def test_max_batch_size_accepted(self, mock_post, mocker):
        strings = [chr(ord("a") + i) * 3 for i in range(SERVICE_CONFIG.max_batch_size)]
        flipped = [s[::-1] for s in strings]
        mock_post.return_value = make_response(mocker, http.HTTPStatus.OK, flipped)
        result = await flip_batch(FlipBatch(strings=strings))
        assert result == FlipBatchResult(strings=flipped)


class TestServerErrors:
    @pytest.mark.asyncio
    async def test_http_500_raises_retryable(self, mock_post, mocker):
        mock_post.return_value = make_response(mocker, http.HTTPStatus.INTERNAL_SERVER_ERROR)
        with pytest.raises(RetryableFlipError):
            await flip_batch(FlipBatch(strings=["hello"]))

    @pytest.mark.asyncio
    async def test_http_400_raises_non_retryable(self, mock_post, mocker):
        mock_post.return_value = make_response(mocker, http.HTTPStatus.BAD_REQUEST)
        with pytest.raises(NonRetryableFlipError):
            await flip_batch(FlipBatch(strings=["hello"]))

    @pytest.mark.asyncio
    async def test_unexpected_status_raises_retryable(self, mock_post, mocker):
        mock_post.return_value = make_response(mocker, http.HTTPStatus.SERVICE_UNAVAILABLE)
        with pytest.raises(RetryableFlipError):
            await flip_batch(FlipBatch(strings=["hello"]))


class TestPartialFailure:
    @pytest.mark.asyncio
    async def test_dash_returned_intact(self, mock_post, mocker):
        mock_post.return_value = make_response(mocker, http.HTTPStatus.OK, ["olleh", "-"])
        result = await flip_batch(FlipBatch(strings=["hello", "world"]))
        assert result == FlipBatchResult(strings=["olleh", "-"])

    @pytest.mark.asyncio
    async def test_all_dashes_returned_intact(self, mock_post, mocker):
        mock_post.return_value = make_response(mocker, http.HTTPStatus.OK, ["-", "-"])
        result = await flip_batch(FlipBatch(strings=["hello", "world"]))
        assert result == FlipBatchResult(strings=["-", "-"])
