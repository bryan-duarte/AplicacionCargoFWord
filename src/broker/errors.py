from __future__ import annotations

from uuid import UUID


class BrokerError(Exception):
    def __init__(self, message: str, operation_uuid: UUID | None = None):
        self.message = message
        self.operation_uuid = operation_uuid
        log_message = (
            f"[operation_uuid={operation_uuid}] {message}"
            if operation_uuid is not None
            else message
        )
        super().__init__(log_message)


class BuyStockError(BrokerError):
    def __init__(self, message: str, operation_uuid: UUID | None = None):
        super().__init__(message, operation_uuid)


class StockNotFoundError(BuyStockError):
    def __init__(self, message: str, operation_uuid: UUID | None = None):
        super().__init__(message, operation_uuid)


class SellStockError(BrokerError):
    def __init__(self, message: str, operation_uuid: UUID | None = None):
        super().__init__(message, operation_uuid)


class BrokerConnectionError(BrokerError):
    """Raised when there is a technical issue connecting to the broker provider."""

    def __init__(self, message: str, operation_uuid: UUID | None = None):
        super().__init__(message, operation_uuid)
