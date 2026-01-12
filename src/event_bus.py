import asyncio
from enum import Enum
from datetime import datetime
from typing import Callable
import logging
from pydantic import BaseModel, Field

class EventType(Enum):
    STOCK_PRICE_CHANGE = "STOCK_PRICE_CHANGE"
    PORTFOLIO_REBALANCE = "PORTFOLIO_REBALANCE"
    
class AsyncEventBus:
    def __init__(self):
        self._listeners = {}

    def subscribe(self, event_type: EventType, callback : Callable):
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(callback)

    async def emit(self, event_type: EventType, event_data: BaseModel):
        if event_type in self._listeners:
            tasks = [callback(event_data) for callback in self._listeners[event_type]]
            await asyncio.gather(*tasks)

bus = AsyncEventBus()

class StockPriceChangeEvent(BaseModel):
    event_type: EventType = EventType.STOCK_PRICE_CHANGE
    event_date: datetime = datetime.now()
    symbol: str = Field(..., min_length=4, max_length=4, description="Symbol of the stock")
    current_price: float = Field(..., gt=0, description="Current price of the stock")
    new_price: float = Field(..., gt=0, description="New price of the stock")
    
    def __repr__(self) -> str:
        return f"StockPriceChangeEvent(symbol={self.symbol}, current_price={self.current_price}, new_price={self.new_price})"
    
class PortfolioRebalanceEvent(BaseModel):
    event_type: EventType = EventType.PORTFOLIO_REBALANCE
    event_date: datetime = datetime.now()
    symbol: str = Field(..., min_length=4, max_length=4, description="Symbol of the stock")
    price: float = Field(..., gt=0, description="Price of the stock")
    
    def __repr__(self) -> str:
        return f"PortfolioRebalanceEvent(symbol={self.symbol}, price={self.price})"
    
async def stock_price_change_handler(event: StockPriceChangeEvent):
    logging.info(f"Stock price changed Alert")
    
async def portfolio_rebalance_handler(event: PortfolioRebalanceEvent):
    logging.info(f"Portfolio rebalanced Alert")
    
