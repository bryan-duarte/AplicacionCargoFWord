from typing import Optional


class PortfolioError(Exception):

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class PortfolioInitializationError(PortfolioError):

    def __init__(
        self,
        message: str,
        failed_operations: Optional[list[str]] = None
    ):
        super().__init__(message)
        self.failed_operations = failed_operations or []


class PortfolioRetryError(PortfolioError):

    def __init__(
        self,
        message: str,
        attempt: int = 0,
        max_attempts: int = 0
    ):
        super().__init__(message)
        self.attempt = attempt
        self.max_attempts = max_attempts

