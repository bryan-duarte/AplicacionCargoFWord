"""Test configuration and fixtures for the financial portfolio management system."""

import asyncio
from collections.abc import Generator
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest

from src.broker.broker import BanChileBroker
from src.broker.broker_interface import Broker
from src.portfolio.portfolio_dtos import PortfolioConfig, StockToAllocate
from src.portfolio.portfolio_register import portfolio_registry
from src.stock.stock import Stock
from src.utils.fake_market import NASDAQ


@pytest.fixture
def event_loop_policy() -> asyncio.AbstractEventLoopPolicy:
    """Provides the default event loop policy for async tests."""
    return asyncio.DefaultEventLoopPolicy()


@pytest.fixture
def valid_stock_symbol() -> str:
    """Provides a valid stock symbol (exactly 4 uppercase letters)."""
    return "AAPL"


@pytest.fixture
def invalid_stock_symbols() -> list[str]:
    """Provides various invalid stock symbols for testing validation."""
    return [
        "AAA",  # Too short (3 chars)
        "AAAAA",  # Too long (5 chars)
        "AA",  # Too short (2 chars)
        "",  # Empty string
        "AAAAAA",  # Too long (6 chars)
        "AA12",  # Contains numbers
        "A1P2",  # Contains numbers
        "AA@L",  # Contains special character
        "    ",  # Only whitespace
    ]


@pytest.fixture
def valid_stock_price() -> Decimal:
    """Provides a valid stock price within the allowed range."""
    return Decimal("150.00")


@pytest.fixture
def minimum_allowed_price() -> Decimal:
    """Provides the minimum valid stock price ($0.01)."""
    return Decimal("0.01")


@pytest.fixture
def maximum_allowed_price() -> Decimal:
    """Provides the maximum valid stock price ($1,000,000)."""
    return Decimal("1000000.00")


@pytest.fixture
def invalid_stock_prices() -> list[Decimal]:
    """Provides various invalid stock prices for testing validation."""
    return [
        Decimal("0.00"),  # Zero price
        Decimal("0.001"),  # Too many decimals
        Decimal("-1.00"),  # Negative price
        Decimal("1000000.01"),  # Above maximum
        Decimal("1000001.00"),  # Above maximum
    ]


@pytest.fixture
def sample_stocks() -> list[Stock]:
    """Provides a list of sample Stock instances for testing."""
    return [
        Stock(symbol="AAPL", price=Decimal("150.00")),
        Stock(symbol="MSFT", price=Decimal("250.00")),
        Stock(symbol="GOOG", price=Decimal("100.00")),
    ]


@pytest.fixture
def sample_portfolio_config(sample_stocks: list[Stock]) -> PortfolioConfig:
    """Provides a sample portfolio configuration with two stock allocations."""
    return PortfolioConfig(
        portfolio_name="Test Portfolio",
        initial_investment=Decimal("10000.00"),
        stocks_to_allocate=[
            StockToAllocate(
                stock=sample_stocks[0], allocation_percentage=Decimal("0.60")
            ),
            StockToAllocate(
                stock=sample_stocks[1], allocation_percentage=Decimal("0.40")
            ),
        ],
    )


@pytest.fixture
def mock_broker() -> AsyncMock:
    """Provides a mocked broker with async methods for testing."""
    broker_mock = AsyncMock(spec=Broker)
    broker_mock.buy_stock_by_amount = AsyncMock()
    broker_mock.buy_stock_by_quantity = AsyncMock()
    broker_mock.sell_stock_by_amount = AsyncMock()
    broker_mock.sell_stock_by_quantity = AsyncMock()
    broker_mock.batch_rollback = AsyncMock(return_value=True)
    return broker_mock


@pytest.fixture
def broker() -> BanChileBroker:
    """Provides a real BanChileBroker instance with zero delay for faster tests."""
    return BanChileBroker(min_delay_seconds=0, max_delay_seconds=0)


@pytest.fixture
def batch_operation_id() -> UUID:
    """Provides a unique identifier for batch operations."""
    return uuid4()


@pytest.fixture(autouse=True)
def reset_registries() -> Generator[None, None, None]:
    """Automatically resets all registries before and after each test.

    This fixture runs automatically (autouse=True) to ensure test isolation
    by clearing the portfolio registry and NASDAQ market state.
    """
    # Setup: Clear before test
    portfolio_registry._portfolios.clear()
    NASDAQ.clear()

    yield

    # Teardown: Clear after test
    portfolio_registry._portfolios.clear()
    NASDAQ.clear()
