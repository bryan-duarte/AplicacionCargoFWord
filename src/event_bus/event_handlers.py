import asyncio
import logging
from src.portfolio.portfolio_register import portfolio_registry
from decimal import Decimal
from src.event_bus.event_dtos import (
    EventType,
    StockPriceChangeEvent,
    PortfolioRebalanceEvent,
)
from src.event_bus.event_bus import bus

# Default threshold for price change alerts (0.00 means always trigger rebalancing)
_DEFAULT_PRICE_CHANGE_ALERT_THRESHOLD_PERCENT = Decimal("0.00")


async def stock_price_change_handler(event: StockPriceChangeEvent):
    logging.info(f"Stock price changed Alert")
    have_significant_change = (
        abs(event.new_price - event.current_price) / event.current_price
        > _DEFAULT_PRICE_CHANGE_ALERT_THRESHOLD_PERCENT
    )
    if have_significant_change:
        await bus.emit(
            EventType.PORTFOLIO_REBALANCE,
            PortfolioRebalanceEvent(symbol=event.symbol, new_price=event.new_price),
        )


async def portfolio_rebalance_handler(event: PortfolioRebalanceEvent):
    logging.info(f"Portfolio rebalanced Alert")
    portfolios_with_stock = await portfolio_registry.get_by_stock_symbol(event.symbol)
    for portfolio in portfolios_with_stock:
        portfolio.update_allocated_stock_price(event.symbol, event.new_price)
        await portfolio.rebalance()
