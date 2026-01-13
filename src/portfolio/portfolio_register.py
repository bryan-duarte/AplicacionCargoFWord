import asyncio
import weakref
import logging


class PortfolioRegistry:
    def __init__(self):
        self._portfolios: set = weakref.WeakSet()

    def add(self, portfolio):
        logging.info(f"Portfolio {portfolio.portfolio_name} added to registry")
        self._portfolios.add(portfolio)

    async def get_by_stock_symbol(self, symbol: str) -> list:
        await asyncio.sleep(0)
        return [
            portfolio
            for portfolio in self._portfolios
            if symbol.upper() in portfolio.allocated_stocks
        ]


portfolio_registry = PortfolioRegistry()
