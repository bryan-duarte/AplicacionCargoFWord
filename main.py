import asyncio
from src.portfolio import Portfolio, StockToAllocate
from src.broker import BanChileBroker
from src.stock import Stock
import logging
from src.event_bus import bus, EventType, stock_price_change_handler, portfolio_rebalance_handler
from src.portfolio_register import portfolio_registry
from src.fake_market import NASDAQ
from decimal import Decimal

logging.basicConfig(level=logging.INFO)

async def main():

    INITIAL_INVESTMENT = 10000
    
    example_portfolio = Portfolio(
        portfolio_name="Risky Pedro",
        initial_investment=INITIAL_INVESTMENT,
        stocks_to_allocate=[
            StockToAllocate(stock=NASDAQ.get("META"), percentage=Decimal("0.2")),
            StockToAllocate(stock=NASDAQ.get("AAPL"), percentage=Decimal("0.4")),
            StockToAllocate(stock=NASDAQ.get("MSFT"), percentage=Decimal("0.4")),
        ],
        broker=BanChileBroker()
    )
    
    bus.subscribe(EventType.STOCK_PRICE_CHANGE, stock_price_change_handler)
    bus.subscribe(EventType.PORTFOLIO_REBALANCE, portfolio_rebalance_handler)

    await example_portfolio.initialize()
    
    logging.info(f"Example portfolio: {example_portfolio}")
    
    await NASDAQ.get("META").set_price_alert("META", Decimal("300"))
    await NASDAQ.get("AAPL").set_price_alert("AAPL", Decimal("200"))
    await NASDAQ.get("MSFT").set_price_alert("MSFT", Decimal("900"))
    
    logging.info(f"Risky Pedro: {example_portfolio}")
    logging.info(f"Risky Pedro total value: {example_portfolio.get_total_value()}")

if __name__ == "__main__":
    asyncio.run(main())
