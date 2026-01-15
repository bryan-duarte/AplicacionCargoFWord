from src.event_bus.event_bus import bus, EventType
from src.event_bus.event_dtos import StockPriceChangeEvent
from src.config.config import settings
from src.stock.errors import InvalidSymbolError, InvalidPriceError
from decimal import Decimal
import re


class Stock:
    def __init__(self, symbol: str, price: Decimal):
        self._symbol = self._validate_symbol(symbol)
        self._price = self._validate_price(price)

    def _validate_symbol(self, symbol: str) -> str:
        """Validate that symbol is exactly 4 uppercase letters."""
        if not isinstance(symbol, str):
            raise InvalidSymbolError(f"Symbol must be a string, got {type(symbol).__name__}")

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

        if price > settings.stock.max_price:
            raise InvalidPriceError(
                f"Price must be at most {settings.stock.max_price}, got {price}"
            )

        return price

    @property
    def symbol(self) -> str:
        return self._symbol

    @property
    def price(self) -> Decimal:
        return self._price

    def current_price(self, new_price: Decimal):
        self._price = new_price

    @classmethod
    async def set_price_alert(cls, symbol: str, new_price: Decimal):
        from src.utils.fake_market import NASDAQ

        if not isinstance(new_price, Decimal):
            new_price = Decimal(str(new_price))

        current_price = NASDAQ.get(symbol).price
        NASDAQ.get(symbol).current_price(new_price)
        await bus.emit(
            EventType.STOCK_PRICE_CHANGE,
            StockPriceChangeEvent(
                new_price=new_price, symbol=symbol, current_price=current_price
            ),
        )

    def __repr__(self) -> str:
        return f"Stock(symbol={self._symbol}, price={self._price})"
