import re
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from src.config.config import settings
from src.stock.errors import InvalidPriceError, InvalidSymbolError

if TYPE_CHECKING:
    from src.utils.fake_market import FakeMarket


class Stock:
    def __init__(
        self,
        symbol: str,
        price: Decimal,
        *,
        market: Optional["FakeMarket"] = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
    ):
        """Initialize a Stock with symbol and price.

        Args:
            symbol: Stock symbol (must be exactly 4 uppercase letters)
            price: Stock price (must be within min/max price limits)
            market: Optional reference to the market this stock belongs to
            min_price: Minimum allowed price (default: 0.01)
            max_price: Maximum allowed price (default: 1000000.00)
        """
        self._symbol = self._validate_symbol(symbol)
        self._min_price = min_price if min_price is not None else Decimal("0.01")
        self._max_price = (
            max_price if max_price is not None else settings.stock.max_price
        )
        self._price = self._validate_price(price)
        self._market = market

    def _validate_symbol(self, symbol: str) -> str:
        """Validate that symbol is exactly 4 uppercase letters."""
        if not isinstance(symbol, str):
            raise InvalidSymbolError(
                f"Symbol must be a string, got {type(symbol).__name__}"
            )

        normalized = symbol.strip().upper()

        if len(normalized) != settings.stock.symbol_max_length:
            raise InvalidSymbolError(
                f"Symbol must be exactly {settings.stock.symbol_max_length} characters, got {len(normalized)}"
            )

        if not re.match(r"^[A-Z]+$", normalized):
            raise InvalidSymbolError(f"Symbol must contain only letters, got: {symbol}")

        return normalized

    def _validate_price(self, price: Decimal) -> Decimal:
        """Validate that price is within acceptable range."""
        if not isinstance(price, Decimal):
            price = Decimal(str(price))

        if price < self._min_price:
            raise InvalidPriceError(
                f"Price must be at least {self._min_price}, got {price}"
            )

        if price > self._max_price:
            raise InvalidPriceError(
                f"Price must be at most {self._max_price}, got {price}"
            )

        return price

    @property
    def symbol(self) -> str:
        return self._symbol

    @property
    def price(self) -> Decimal:
        return self._price

    def current_price(self, new_price: Decimal) -> None:
        """Update the stock price.

        Note: No explicit sync with market needed because FakeMarket
        maintains a direct reference to this Stock object.
        Changes are reflected automatically.
        """
        self._price = self._validate_price(new_price)

    def __repr__(self) -> str:
        return f"Stock(symbol={self._symbol}, price={self._price})"
