class StockError(Exception):
    """Base exception for Stock-related errors."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class InvalidSymbolError(StockError):
    """Raised when a stock symbol is invalid."""

    def __init__(self, message: str):
        super().__init__(message)


class InvalidPriceError(StockError):
    """Raised when a stock price is invalid."""

    def __init__(self, message: str):
        super().__init__(message)
