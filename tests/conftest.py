"""Test configuration and fixtures for the financial portfolio management system."""

import asyncio
from collections.abc import Generator
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest

from src.broker.broker import BanChileBroker
from src.broker.broker_dtos import (
    BatchOperationEntry,
    BuyStockByAmountRequest,
    BuyStockByQuantityRequest,
    BuyStockResponse,
    OperationState,
    SellStockByQuantityRequest,
    SellStockResponse,
)
from src.broker.broker_interface import Broker
from src.portfolio.portfolio_dtos import PortfolioConfig, StockToAllocate
from src.portfolio.portfolio_register import portfolio_registry
from src.stock.stock import Stock
from src.utils.decimal_utils import quantize_money, quantize_quantity
from src.utils.fake_market import NASDAQ


class DummyBroker(Broker):
    """Dummy broker implementation for testing with controllable behavior."""

    def __init__(
        self,
        *,
        market: dict[str, Decimal],
        fail_on_nth_buy: int | None = None,
        latency_seconds: float = 0.0,
    ):
        self._market_prices: dict[str, Decimal] = market.copy() if market else {}
        self._batch_operations: dict[str, dict[str, BatchOperationEntry]] = {}
        self._total_buy_operations: int = 0
        self._total_sell_operations: int = 0
        self._failure_trigger_threshold: int | None = fail_on_nth_buy
        self._network_latency_seconds: float = latency_seconds
        self._rollback_was_invoked: bool = False
        self._last_rolled_back_batch_id: str | None = None

    def _get_current_stock_price(self, stock_symbol: str) -> Decimal:
        """Get the current market price for a stock symbol."""
        return self._market_prices.get(stock_symbol, Decimal("100.00"))

    async def buy_stock_by_amount(
        self, request: BuyStockByAmountRequest
    ) -> BuyStockResponse:
        """Buy stock by amount with simulated network latency."""
        await self._simulate_network_latency()

        stock_price = self._get_current_stock_price(request.symbol)
        purchased_quantity = quantize_quantity(request.amount / stock_price)

        buy_response = BuyStockResponse(
            uuid=request.uuid,
            symbol=request.symbol,
            amount=request.amount,
            price=stock_price,
            quantity=purchased_quantity,
            batch_uuid=request.batch_uuid,
        )

        self._register_batch_operation(request, buy_response)
        return buy_response

    async def buy_stock_by_quantity(
        self, request: BuyStockByQuantityRequest
    ) -> BuyStockResponse:
        """Buy stock by quantity with optional failure simulation."""
        self._total_buy_operations += 1

        self._check_for_simulated_failure()

        await self._simulate_network_latency()

        stock_price = self._get_current_stock_price(request.symbol)
        quantized_quantity = quantize_quantity(request.quantity)

        buy_response = BuyStockResponse(
            uuid=request.uuid,
            symbol=request.symbol,
            amount=quantize_money(stock_price * quantized_quantity),
            price=stock_price,
            quantity=quantized_quantity,
            batch_uuid=request.batch_uuid,
        )

        self._register_batch_operation(request, buy_response)
        return buy_response

    async def sell_stock_by_amount(self, request) -> SellStockResponse:
        """Sell stock by amount (not implemented)."""
        raise NotImplementedError()

    async def sell_stock_by_quantity(
        self, request: SellStockByQuantityRequest
    ) -> SellStockResponse:
        """Sell stock by quantity with simulated network latency."""
        self._total_sell_operations += 1

        await self._simulate_network_latency()

        stock_price = self._get_current_stock_price(request.symbol)
        quantized_quantity = quantize_quantity(request.quantity)

        sell_response = SellStockResponse(
            uuid=request.uuid,
            symbol=request.symbol,
            amount=quantize_money(stock_price * quantized_quantity),
            price=stock_price,
            quantity=quantized_quantity,
            batch_uuid=request.batch_uuid,
        )

        self._register_batch_operation(request, sell_response)
        return sell_response

    def _check_for_simulated_failure(self) -> None:
        """Raise exception if configured failure threshold is reached."""
        if (
            self._failure_trigger_threshold is not None
            and self._total_buy_operations >= self._failure_trigger_threshold
        ):
            raise Exception(
                f"Simulated failure on buy operation {self._total_buy_operations}"
            )

    async def _simulate_network_latency(self) -> None:
        """Simulate network delay if configured."""
        if self._network_latency_seconds > 0:
            await asyncio.sleep(self._network_latency_seconds)

    def _register_batch_operation(
        self,
        request: BuyStockByAmountRequest
        | BuyStockByQuantityRequest
        | SellStockByQuantityRequest,
        response: BuyStockResponse | SellStockResponse,
    ) -> None:
        """Register an operation in the batch registry for potential rollback."""
        batch_id = getattr(request, "batch_uuid", None)

        if not batch_id:
            return

        if batch_id not in self._batch_operations:
            self._batch_operations[batch_id] = {}

        self._batch_operations[batch_id][request.uuid] = BatchOperationEntry(
            operation_uuid=request.uuid,
            operation_schema=request,
            state=OperationState.SUCCESS,
            response=response,
        )

    async def batch_rollback(self, batch_uuid: str) -> bool:
        """Rollback all operations in a batch."""
        self._rollback_was_invoked = True
        self._last_rolled_back_batch_id = batch_uuid

        if batch_uuid not in self._batch_operations:
            return False

        for batch_entry in self._batch_operations[batch_uuid].values():
            batch_entry.state = OperationState.ROLLED_BACK

        del self._batch_operations[batch_uuid]
        return True

    @property
    def rollback_called(self) -> bool:
        """Check if rollback was invoked at least once."""
        return self._rollback_was_invoked

    @property
    def last_rollback_batch_uuid(self) -> str | None:
        """Get the batch UUID of the last rollback operation."""
        return self._last_rolled_back_batch_id

    @property
    def buy_operation_count(self) -> int:
        """Get the total number of buy operations performed."""
        return self._total_buy_operations

    @property
    def sell_operation_count(self) -> int:
        """Get the total number of sell operations performed."""
        return self._total_sell_operations

    def reset_counters(self) -> None:
        """Reset all operation counters and rollback tracking."""
        self._total_buy_operations = 0
        self._total_sell_operations = 0
        self._rollback_was_invoked = False


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
