"""Event bus DTOs."""
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from decimal import Decimal
from src.config.config import settings


class EventType(Enum):
    STOCK_PRICE_CHANGE = "STOCK_PRICE_CHANGE"
    PORTFOLIO_REBALANCE = "PORTFOLIO_REBALANCE"


class StockPriceChangeEvent(BaseModel):
    model_config = ConfigDict(frozen=True)

    event_type: EventType = EventType.STOCK_PRICE_CHANGE
    event_date: datetime = Field(default_factory=datetime.now)
    symbol: str = Field(
        ...,
        min_length=4,
        max_length=4,
        description="Symbol of the stock (4 uppercase letters)"
    )
    current_price: Decimal = Field(
        ...,
        gt=0,
        max_digits=settings.pydantic_constraints.money,
        decimal_places=settings.decimal_precision.money,
        description="Current price of the stock (USD)"
    )
    new_price: Decimal = Field(
        ...,
        gt=0,
        max_digits=settings.pydantic_constraints.money,
        decimal_places=settings.decimal_precision.money,
        description="New price of the stock (USD)"
    )

    def __repr__(self) -> str:
        return f"StockPriceChangeEvent(symbol={self.symbol}, current_price={self.current_price}, new_price={self.new_price})"


class PortfolioRebalanceEvent(BaseModel):
    model_config = ConfigDict(frozen=True)

    event_type: EventType = EventType.PORTFOLIO_REBALANCE
    event_date: datetime = Field(default_factory=datetime.now)
    symbol: str = Field(
        ...,
        min_length=4,
        max_length=4,
        description="Symbol of the stock 4 uppercase letters"
    )
    new_price: Decimal = Field(
        ...,
        gt=0,
        max_digits=settings.pydantic_constraints.money,
        decimal_places=settings.decimal_precision.money,
        description="New price of the stock USD"
    )
