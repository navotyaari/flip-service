import temporalio.exceptions


class RetryableFlipError(Exception):
    pass


class NonRetryableFlipError(temporalio.exceptions.ApplicationError):
    def __init__(self, message: str):
        super().__init__(message, non_retryable=True)
