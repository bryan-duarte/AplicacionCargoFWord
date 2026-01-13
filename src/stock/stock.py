from src.event_bus.event_bus import bus, EventType
from src.event_bus.event_dtos import StockPriceChangeEvent
from decimal import Decimal


class Stock:
    def __init__(self, symbol: str, price: Decimal):
        self._symbol = symbol
        self._price = price

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
        from src.fake_market.fake_market import NASDAQ

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
