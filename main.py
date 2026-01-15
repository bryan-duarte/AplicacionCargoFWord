import asyncio
from src.portfolio.portfolio import Portfolio, StockToAllocate
from src.portfolio.portfolio_dtos import PortfolioConfig
from src.broker.broker import BanChileBroker
import logging
from src.event_bus.event_bus import bus, EventType
from src.event_bus.event_handlers import (
    stock_price_change_handler,
    portfolio_rebalance_handler,
)
from src.utils.fake_market import NASDAQ
from decimal import Decimal

logging.basicConfig(level=logging.INFO)


async def main():
    INITIAL_INVESTMENT = 10000

    config = PortfolioConfig(
        portfolio_name="Risky Pedro",
        initial_investment=Decimal(str(INITIAL_INVESTMENT)),
        stocks_to_allocate=[
            StockToAllocate(stock=NASDAQ.get("META"), allocation_percentage=Decimal("0.2")),
            StockToAllocate(stock=NASDAQ.get("AAPL"), allocation_percentage=Decimal("0.4")),
            StockToAllocate(stock=NASDAQ.get("MSFT"), allocation_percentage=Decimal("0.4")),
        ],
    )

    risky_pedro_portfolio = Portfolio(config=config, broker=BanChileBroker())

    bus.subscribe(EventType.STOCK_PRICE_CHANGE, stock_price_change_handler)
    bus.subscribe(EventType.PORTFOLIO_REBALANCE, portfolio_rebalance_handler)

    await risky_pedro_portfolio.initialize()

    logging.info(f"Risky Pedro portfolio before price alerts: {risky_pedro_portfolio}")

    await NASDAQ.get("META").set_price_alert("META", Decimal("300"))
    await NASDAQ.get("AAPL").set_price_alert("AAPL", Decimal("200"))
    await NASDAQ.get("MSFT").set_price_alert("MSFT", Decimal("900"))

    logging.info(f"Risky Pedro total value: {risky_pedro_portfolio.get_total_value()}")
    logging.info(f"Risky Pedro: {risky_pedro_portfolio}")


if __name__ == "__main__":
    asyncio.run(main())
