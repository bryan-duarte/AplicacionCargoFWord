"""Integration tests for large-scale portfolio registry rebalancing."""

import logging
import random
from decimal import Decimal

import pytest

from src.portfolio.portfolio import Portfolio
from src.portfolio.portfolio_dtos import PortfolioConfig, StockToAllocate
from src.portfolio.portfolio_register import PortfolioRegistry
from src.stock.stock import Stock
from src.utils.decimal_utils import quantize_money, quantize_percentage
from tests.conftest import DummyBroker

RANDOM_SEED = 42
NUM_PORTFOLIOS = 100
NUM_STOCKS = 50
PRICE_CHANGE_MIN = Decimal("-0.03")
PRICE_CHANGE_MAX = Decimal("0.03")
ALLOCATION_TOLERANCE = Decimal("0.001")
MIN_PRICE = Decimal("10.00")
MAX_PRICE = Decimal("1000.00")
INITIAL_INVESTMENT = Decimal("10000.00")
REBALANCE_THRESHOLD = Decimal("0.01")


def _generate_stock_symbol(index: int) -> str:
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    first_char = alphabet[(index // 26) % 26]
    second_char = alphabet[index % 26]
    return f"ST{first_char}{second_char}"


def _generate_random_allocations(count: int) -> list[Decimal]:
    random_values = [random.random() for _ in range(count)]
    total_sum = sum(random_values)

    normalized_values = [Decimal(str(value / total_sum)) for value in random_values[:-1]]
    allocations = [quantize_percentage(value) for value in normalized_values]

    remaining_allocation = Decimal("1.0") - sum(allocations)
    allocations.append(quantize_percentage(remaining_allocation))

    return allocations


def _create_random_stocks(count: int) -> dict[str, Stock]:
    stocks = {}
    for stock_index in range(count):
        symbol = _generate_stock_symbol(stock_index)
        random_price = Decimal(str(random.uniform(float(MIN_PRICE), float(MAX_PRICE))))
        price = quantize_money(random_price)
        stocks[symbol] = Stock(symbol=symbol, price=price)
    return stocks


def _apply_random_price_change(stock: Stock) -> None:
    price_change_percent = Decimal(str(random.uniform(float(PRICE_CHANGE_MIN), float(PRICE_CHANGE_MAX))))
    new_price = stock.price * (Decimal("1") + price_change_percent)
    clamped_price = max(MIN_PRICE, min(MAX_PRICE, new_price))
    final_price = quantize_money(clamped_price)
    stock.current_price(final_price)


def _create_portfolio(portfolio_index: int, available_stocks: dict[str, Stock], registry: PortfolioRegistry) -> Portfolio:
    num_stocks_in_portfolio = random.randint(10, 50)
    selected_symbols = random.sample(list(available_stocks.keys()), num_stocks_in_portfolio)
    allocations = _generate_random_allocations(num_stocks_in_portfolio)

    stocks_to_allocate = [
        StockToAllocate(stock=available_stocks[symbol], allocation_percentage=allocations[symbol_index])
        for symbol_index, symbol in enumerate(selected_symbols)
    ]

    portfolio_name = f"Portfolio_{portfolio_index}"
    initial_market_prices = {symbol: available_stocks[symbol].price for symbol in selected_symbols}
    broker = DummyBroker(market=initial_market_prices, latency_seconds=0.01)

    config = PortfolioConfig(
        portfolio_name=portfolio_name,
        initial_investment=INITIAL_INVESTMENT,
        stocks_to_allocate=stocks_to_allocate,
    )

    return Portfolio(config, broker, registry=registry, rebalance_threshold=REBALANCE_THRESHOLD)


async def _create_and_initialize_portfolios(count: int, available_stocks: dict[str, Stock], registry: PortfolioRegistry) -> list[Portfolio]:
    portfolios = [_create_portfolio(portfolio_index, available_stocks, registry) for portfolio_index in range(1, count + 1)]

    for portfolio in portfolios:
        await portfolio.initialize()

    return portfolios


def _verify_portfolio_is_balanced(portfolio: Portfolio, tolerance: Decimal = ALLOCATION_TOLERANCE) -> None:
    total_portfolio_value = portfolio.get_total_value().total_value

    for allocated_stock in portfolio.allocated_stocks.values():
        actual_stock_allocation = allocated_stock.total_value / total_portfolio_value
        target_allocation = allocated_stock.allocation_percentage
        allocation_deviation = abs(actual_stock_allocation - target_allocation)

        stock_is_within_tolerance = allocation_deviation <= tolerance

        assert stock_is_within_tolerance, (
            f"Portfolio '{portfolio.portfolio_name}': Stock '{allocated_stock.stock.symbol}' "
            f"allocation {actual_stock_allocation:.6f} differs from target {target_allocation:.6f} "
            f"by {allocation_deviation:.6f} (tolerance: {tolerance:.6f})"
        )

    logging.info(
        f"✓ Portfolio '{portfolio.portfolio_name}' is BALANCED - "
        f"Total value: ${total_portfolio_value:.2f}, "
        f"Stocks: {len(portfolio.allocated_stocks)}"
    )


async def _rebalance_portfolios_holding_symbol(stocks: dict[str, Stock], registry: PortfolioRegistry, symbol: str) -> None:
    affected_portfolios = await registry.get_by_stock_symbol(symbol)
    updated_price = stocks[symbol].price

    logging.debug(f"Rebalancing {len(affected_portfolios)} portfolios holding '{symbol}' at new price ${updated_price:.2f}")

    for portfolio in affected_portfolios:
        portfolio.update_allocated_stock_price(symbol, updated_price)
        await portfolio.rebalance()


async def _apply_price_changes_to_stocks_and_rebalance(
    stocks: dict[str, Stock],
    registry: PortfolioRegistry,
    portfolios: list[Portfolio],
    symbols_to_change: list[str],
    wave_name: str,
) -> None:
    logging.info(f"Starting '{wave_name}': Applying {len(symbols_to_change)} price changes")

    for symbol in symbols_to_change:
        old_price = stocks[symbol].price
        _apply_random_price_change(stocks[symbol])
        new_price = stocks[symbol].price
        price_change_percent = ((new_price - old_price) / old_price) * 100

        logging.debug(
            f"Price change for '{symbol}': ${old_price:.2f} -> ${new_price:.2f} "
            f"({price_change_percent:+.2f}%)"
        )

        await _rebalance_portfolios_holding_symbol(stocks, registry, symbol)

    logging.info(f"Finished '{wave_name}': Verifying all {len(portfolios)} portfolios are balanced")

    for portfolio in portfolios:
        _verify_portfolio_is_balanced(portfolio)

    logging.info(f"✓ '{wave_name}' complete: All {len(portfolios)} portfolios verified as balanced")


@pytest.mark.slow
@pytest.mark.asyncio
async def test_large_scale_rebalancing_with_many_portfolios() -> None:
    logging.info("=" * 80)
    logging.info("LARGE-SCALE REGISTRY REBALANCING TEST")
    logging.info("=" * 80)
    logging.info(f"Configuration: {NUM_PORTFOLIOS} portfolios, {NUM_STOCKS} stocks")
    logging.info(f"Price change range: {PRICE_CHANGE_MIN}% to {PRICE_CHANGE_MAX}%")
    logging.info(f"Allocation tolerance: {ALLOCATION_TOLERANCE}%")
    logging.info("")

    random.seed(RANDOM_SEED)

    logging.info(f"Creating {NUM_STOCKS} stocks...")
    isolated_registry = PortfolioRegistry()
    available_stocks = _create_random_stocks(NUM_STOCKS)
    logging.info(f"✓ Created {len(available_stocks)} stocks")

    logging.info(f"Creating {NUM_PORTFOLIOS} portfolios with isolated registry...")
    portfolios = await _create_and_initialize_portfolios(NUM_PORTFOLIOS, available_stocks, isolated_registry)
    logging.info(f"✓ Created and initialized {len(portfolios)} portfolios")
    logging.info("")

    wave_1_symbols = random.sample(list(available_stocks.keys()), 10)
    await _apply_price_changes_to_stocks_and_rebalance(available_stocks, isolated_registry, portfolios, wave_1_symbols, "Wave 1 (10 changes)")

    wave_2_symbols = random.sample(list(available_stocks.keys()), 20)
    await _apply_price_changes_to_stocks_and_rebalance(available_stocks, isolated_registry, portfolios, wave_2_symbols, "Wave 2 (20 changes)")

    wave_3_symbols = [random.choice(list(available_stocks.keys())) for _ in range(100)]
    await _apply_price_changes_to_stocks_and_rebalance(available_stocks, isolated_registry, portfolios, wave_3_symbols, "Wave 3 (100 changes)")

    logging.info("")
    logging.info("=" * 80)
    logging.info("TEST PASSED: All waves completed successfully")
    logging.info("=" * 80)
    logging.info(f"Final verification: All {len(portfolios)} portfolios remain balanced after {len(wave_1_symbols) + len(wave_2_symbols) + len(wave_3_symbols)} total price changes")
