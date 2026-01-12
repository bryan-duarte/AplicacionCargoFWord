import asyncio
from src.portfolio import Portfolio, StockToAllocate
from src.broker import BanChileBroker, FAKE_MARKET
from src.stock import Stock
import logging
from src.event_bus import bus, EventType, stock_price_change_handler, portfolio_rebalance_handler
from src.portfolio_register import portfolio_registry

logging.basicConfig(level=logging.INFO)

async def main():

    INITIAL_INVESTMENT = 10000
    
    META_STOCK = Stock(symbol="META", price=FAKE_MARKET["META"])
    AAPL_STOCK = Stock(symbol="AAPL", price=FAKE_MARKET["AAPL"])
    MSFT_STOCK = Stock(symbol="MSFT", price=FAKE_MARKET["MSFT"])
    TSLA_STOCK = Stock(symbol="TSLA", price=FAKE_MARKET["TSLA"])
    AMZN_STOCK = Stock(symbol="AMZN", price=FAKE_MARKET["AMZN"])
    
    example_portfolio = Portfolio(
        portfolio_name="Risky Pedro",
        initial_investment=INITIAL_INVESTMENT,
        stocks_to_allocate=[
            StockToAllocate(stock=META_STOCK, percentage=0.4),
            StockToAllocate(stock=AAPL_STOCK, percentage=0.6),
        ],
        broker=BanChileBroker()
    )
    
    moderate_portfolio = Portfolio(
        portfolio_name="Moderate Pedro",
        initial_investment=INITIAL_INVESTMENT,
        stocks_to_allocate=[
            StockToAllocate(stock=META_STOCK, percentage=0.2),
            StockToAllocate(stock=AAPL_STOCK, percentage=0.2),
            StockToAllocate(stock=MSFT_STOCK, percentage=0.2),
            StockToAllocate(stock=TSLA_STOCK, percentage=0.2),
            StockToAllocate(stock=AMZN_STOCK, percentage=0.2),
        ],
        broker=BanChileBroker()
    )
    
    bus.subscribe(EventType.STOCK_PRICE_CHANGE, stock_price_change_handler)
    bus.subscribe(EventType.PORTFOLIO_REBALANCE, portfolio_rebalance_handler)

    await example_portfolio.initialize()
    await moderate_portfolio.initialize()
    
    await META_STOCK.current_price(FAKE_MARKET[META_STOCK.symbol] * 1.1)
    
    portfolios_with_meta = await portfolio_registry.get_by_stock_symbol(META_STOCK.symbol)
    
    logging.info(f"Portfolios with META: {portfolios_with_meta}")


if __name__ == "__main__":
    asyncio.run(main())
