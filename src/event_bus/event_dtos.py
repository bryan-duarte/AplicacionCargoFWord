from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field
from decimal import Decimal


class EventType(Enum):
    STOCK_PRICE_CHANGE = "STOCK_PRICE_CHANGE"
    PORTFOLIO_REBALANCE = "PORTFOLIO_REBALANCE"


class StockPriceChangeEvent(BaseModel):
    event_type: EventType = EventType.STOCK_PRICE_CHANGE
    event_date: datetime = datetime.now()
    symbol: str = Field(
        ..., min_length=4, max_length=4, description="Symbol of the stock"
    )
    current_price: Decimal = Field(..., gt=0, description="Current price of the stock")
    new_price: Decimal = Field(..., gt=0, description="New price of the stock")

    def __repr__(self) -> str:
        return f"StockPriceChangeEvent(symbol={self.symbol}, current_price={self.current_price}, new_price={self.new_price})"


class PortfolioRebalanceEvent(BaseModel):
    event_type: EventType = EventType.PORTFOLIO_REBALANCE
    event_date: datetime = datetime.now()
    symbol: str = Field(
        ..., min_length=4, max_length=4, description="Symbol of the stock"
    )
    new_price: Decimal = Field(..., gt=0, description="New price of the stock")

    def __repr__(self) -> str:
        return (
            f"PortfolioRebalanceEvent(symbol={self.symbol}, new_price={self.new_price})"
        )
