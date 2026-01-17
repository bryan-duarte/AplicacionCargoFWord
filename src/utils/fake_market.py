from decimal import Decimal

from src.stock.stock import Stock


class FakeMarket:
    """Fake market simulating NASDAQ stock exchange."""

    def __init__(self) -> None:
        self._stocks: dict[str, Stock] = {}

    def register(self, stock: Stock) -> None:
        """Register a stock in the market."""
        self._stocks[stock.symbol] = stock

    def get(self, symbol: str) -> Stock | None:
        """Get a stock by symbol."""
        return self._stocks.get(symbol.upper())

    def clear(self) -> None:
        """Clear all stocks from the market (used in tests)."""
        self._stocks.clear()


NASDAQ = FakeMarket()
NASDAQ.register(Stock(symbol="AAPL", price=Decimal("250"), market=NASDAQ))
NASDAQ.register(Stock(symbol="META", price=Decimal("150"), market=NASDAQ))
NASDAQ.register(Stock(symbol="MSFT", price=Decimal("600"), market=NASDAQ))
NASDAQ.register(Stock(symbol="TSLA", price=Decimal("100"), market=NASDAQ))
NASDAQ.register(Stock(symbol="AMZN", price=Decimal("150"), market=NASDAQ))
