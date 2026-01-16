import asyncio
from src.portfolio.portfolio import Portfolio, StockToAllocate
from src.portfolio.portfolio_dtos import PortfolioConfig
from src.portfolio.portfolio_register import portfolio_registry
from src.broker.broker import BanChileBroker
import logging
from src.utils.fake_market import NASDAQ
from decimal import Decimal

logging.basicConfig(level=logging.INFO)


async def rebalance_affected_portfolios(symbol: str, new_price: Decimal) -> None:
    """Rebalance all portfolios that contain the given stock."""
    logging.info(f"Rebalancing portfolios for {symbol} at ${new_price}")
    portfolios = await portfolio_registry.get_by_stock_symbol(symbol)
    for portfolio in portfolios:
        portfolio.update_allocated_stock_price(symbol, new_price)
        await portfolio.rebalance()


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
    await risky_pedro_portfolio.initialize()

    logging.info(f"Risky Pedro portfolio before price alerts: {risky_pedro_portfolio}")

    # ──────────────────────────────────────────────────────────────
    # ESCENARIO 1: Cambio único con rebalanceo inmediato
    # ──────────────────────────────────────────────────────────────
    logging.info("\n=== ESCENARIO 1: META price change + rebalance inmediato ===")
    NASDAQ.get("META").current_price(Decimal("300"))
    await rebalance_affected_portfolios("META", Decimal("300"))

    # ──────────────────────────────────────────────────────────────
    # ESCENARIO 2: Múltiples cambios SIN rebalanceo, luego UN rebalance
    # ──────────────────────────────────────────────────────────────
    logging.info("\n=== ESCENARIO 2: 3 cambios de AAPL sin rebalanceo ===")

    # Primer cambio de AAPL (sin rebalanceo)
    NASDAQ.get("AAPL").current_price(Decimal("180"))
    logging.info(f"AAPL cambió a $180 (sin rebalanceo)")

    # Segundo cambio de AAPL (sin rebalanceo)
    NASDAQ.get("AAPL").current_price(Decimal("190"))
    logging.info(f"AAPL cambió a $190 (sin rebalanceo)")

    # Tercer cambio de AAPL (sin rebalanceo)
    NASDAQ.get("AAPL").current_price(Decimal("200"))
    logging.info(f"AAPL cambió a $200 (sin rebalanceo)")

    # AHORA sí rebalanceamos con el precio final
    logging.info("=== Ahora ejecutamos el rebalanceo con el precio final ===")
    await rebalance_affected_portfolios("AAPL", Decimal("200"))

    # ──────────────────────────────────────────────────────────────
    # ESCENARIO 3: Cambio normal de MSFT
    # ──────────────────────────────────────────────────────────────
    logging.info("\n=== ESCENARIO 3: MSFT price change + rebalance inmediato ===")
    NASDAQ.get("MSFT").current_price(Decimal("900"))
    await rebalance_affected_portfolios("MSFT", Decimal("900"))

    logging.info(f"\nRisky Pedro total value: {risky_pedro_portfolio.get_total_value()}")
    logging.info(f"Risky Pedro: {risky_pedro_portfolio}")


if __name__ == "__main__":
    asyncio.run(main())
