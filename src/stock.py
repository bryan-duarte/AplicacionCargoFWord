import asyncio
from src.event_bus import bus, EventType, StockPriceChangeEvent


class Stock:
    def __init__(self, symbol: str, price: float):
        self._symbol = symbol
        self._price = price
        
    @property
    def symbol(self) -> str:
        return self._symbol
    
    @property
    def price(self) -> float:
        return self._price
    
    async def current_price(self, new_price: float):
        current_price = self._price
        self._price = new_price
        
        await bus.emit(
            EventType.STOCK_PRICE_CHANGE,
            StockPriceChangeEvent(
                current_price=current_price,
                new_price=new_price,
                symbol=self._symbol
            )
        )
        
    def __repr__(self) -> str:
        return f"Stock(symbol={self._symbol}, price={self._price})"