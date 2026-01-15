from typing import Optional
from uuid import UUID

class PortfolioError(Exception):
    """Base exception for portfolio-related errors."""

    def __init__(self, message: str, operation_uuid: Optional[UUID] = None):
        self.message = message
        self.operation_uuid = operation_uuid
        log_message = (
            f"[operation_uuid={operation_uuid}] {message}"
            if operation_uuid is not None
            else message
        )
        super().__init__(log_message)

class PortfolioInitializationError(PortfolioError):
    """Raised when portfolio initialization fails completely."""

    def __init__(
        self,
        message: str,
        operation_uuid: Optional[UUID] = None,
        failed_operations: Optional[list[str]] = None
    ):
        super().__init__(message, operation_uuid)
        self.failed_operations = failed_operations or []

class PortfolioRetryError(PortfolioError):
    """Raised when retry logic fails after all attempts."""

    def __init__(
        self,
        message: str,
        operation_uuid: Optional[UUID] = None,
        attempt: int = 0,
        max_attempts: int = 0
    ):
        super().__init__(message, operation_uuid)
        self.attempt = attempt
        self.max_attempts = max_attempts
