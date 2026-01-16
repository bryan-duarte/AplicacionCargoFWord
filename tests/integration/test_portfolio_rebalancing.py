"""Integration tests for portfolio rebalancing functionality."""
import asyncio
from decimal import Decimal
import pytest
import logging
from src.broker.broker import BanChileBroker
from src.broker.broker_dtos import (
    BuyStockByAmountRequest,
    BuyStockByQuantityRequest,
    SellStockByQuantityRequest,
    BuyStockResponse,
    SellStockResponse,
    BatchOperationEntry,
    OperationState,
)
from src.broker.broker_interface import Broker
from src.portfolio.portfolio import Portfolio
from src.portfolio.portfolio_dtos import PortfolioConfig, StockToAllocate
from src.portfolio.errors import PortfolioError, PortfolioInitializationError
from src.stock.stock import Stock
from src.utils.fake_market import NASDAQ
from src.utils.decimal_utils import quantize_money, quantize_quantity


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

    async def buy_stock_by_amount(self, request: BuyStockByAmountRequest) -> BuyStockResponse:
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

    async def buy_stock_by_quantity(self, request: BuyStockByQuantityRequest) -> BuyStockResponse:
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

    async def sell_stock_by_quantity(self, request: SellStockByQuantityRequest) -> SellStockResponse:
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
            raise Exception(f"Simulated failure on buy operation {self._total_buy_operations}")

    async def _simulate_network_latency(self) -> None:
        """Simulate network delay if configured."""
        if self._network_latency_seconds > 0:
            await asyncio.sleep(self._network_latency_seconds)

    def _register_batch_operation(
        self,
        request: BuyStockByAmountRequest | BuyStockByQuantityRequest | SellStockByQuantityRequest,
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

    def get_successful_operations(self, batch_uuid: str) -> list[BatchOperationEntry]:
        """Get all successful or rolled-back operations for a batch."""
        if batch_uuid not in self._batch_operations:
            return []

        completed_states = {OperationState.SUCCESS, OperationState.ROLLED_BACK}
        return [
            entry
            for entry in self._batch_operations[batch_uuid].values()
            if entry.state in completed_states
        ]


class FailingRollbackBroker(DummyBroker):
    """Broker that fails on rollback for testing stale state scenarios."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._rollback_failure_enabled: bool = True
        self._executed_partial_operations: list[dict] = []

    async def buy_stock_by_quantity(self, request: BuyStockByQuantityRequest) -> BuyStockResponse:
        """Track partial operations before potential failure."""
        try:
            buy_result = await super().buy_stock_by_quantity(request)

            self._executed_partial_operations.append({
                "operation_type": "BUY",
                "stock_symbol": buy_result.symbol,
                "traded_quantity": buy_result.quantity,
                "associated_batch_uuid": request.batch_uuid,
            })

            return buy_result
        except Exception:
            raise

    async def batch_rollback(self, batch_uuid: str) -> bool:
        """Override to simulate rollback failure."""
        await super().batch_rollback(batch_uuid)

        # Return False to indicate rollback failure
        return not self._rollback_failure_enabled

    def enable_successful_rollback(self) -> None:
        """Allow rollbacks to succeed for testing."""
        self._rollback_failure_enabled = False

    def get_partial_operations(self, batch_uuid: str) -> list[dict]:
        """Retrieve all partial operations for a specific batch."""
        return [
            operation
            for operation in self._executed_partial_operations
            if operation.get("associated_batch_uuid") == batch_uuid
        ]


class TestSimplePortfolioRebalancing:

    @pytest.mark.asyncio
    async def test_simple_rebalancing_maintains_correct_distribution(
        self, sample_portfolio_config: PortfolioConfig, reset_registries
    ):
        initial_market_prices = {
            "AAPL": Decimal("150.00"),
            "MSFT": Decimal("300.00"),
            "GOOG": Decimal("2500.00"),
            "TSLA": Decimal("800.00"),
            "AMZN": Decimal("3200.00"),
        }

        updated_prices = {
            "AAPL": Decimal("200.00"),
            "MSFT": Decimal("250.00"),
        }

        broker = DummyBroker(market=initial_market_prices, latency_seconds=0.01)

        portfolio = Portfolio(
            config=sample_portfolio_config,
            broker=broker,
            rebalance_threshold=Decimal("0.01"),
        )

        await portfolio.initialize()

        initial_stock_quantities = {
            symbol: stock.quantity
            for symbol, stock in portfolio.allocated_stocks.items()
        }

        for symbol, new_price in updated_prices.items():
            portfolio.update_allocated_stock_price(symbol, new_price)

        await portfolio.rebalance()

        final_total_value = portfolio.get_total_value().total_value
        tolerance_percentage = Decimal("0.001")

        for symbol, allocated_stock in portfolio.allocated_stocks.items():
            current_allocation_percentage = allocated_stock.total_value / final_total_value
            target_allocation_percentage = allocated_stock.allocation_percentage
            allocation_deviation = abs(
                current_allocation_percentage - target_allocation_percentage
            )

            assert allocation_deviation <= tolerance_percentage, (
                f"Stock {symbol} allocation percentage is off target. "
                f"Expected: {target_allocation_percentage:.4%}, "
                f"Actual: {current_allocation_percentage:.4%}, "
                f"Difference: {allocation_deviation:.4%}"
            )

        final_stock_quantities = {
            symbol: stock.quantity
            for symbol, stock in portfolio.allocated_stocks.items()
        }

        stock_quantities_changed = any(
            final_stock_quantities[symbol] != initial_stock_quantities[symbol]
            for symbol in initial_stock_quantities
        )

        assert stock_quantities_changed, (
            "Expected at least one stock quantity to change after price changes and rebalance"
        )

        assert portfolio.is_locked is False, "Lock should be released after rebalance completes"

    @pytest.mark.asyncio
    async def test_no_rebalancing_when_prices_stable(
        self, sample_portfolio_config: PortfolioConfig, reset_registries
    ):
        market_prices = {
            "AAPL": Decimal("150.00"),
            "MSFT": Decimal("300.00"),
            "GOOG": Decimal("2500.00"),
            "TSLA": Decimal("800.00"),
            "AMZN": Decimal("3200.00"),
        }

        broker = DummyBroker(market=market_prices)

        portfolio = Portfolio(
            config=sample_portfolio_config,
            broker=broker,
            rebalance_threshold=Decimal("0.01"),
        )

        await portfolio.initialize()

        initial_stock_quantities = {
            symbol: stock.quantity
            for symbol, stock in portfolio.allocated_stocks.items()
        }

        await portfolio.rebalance()

        for symbol, stock in portfolio.allocated_stocks.items():
            final_quantity = stock.quantity
            initial_quantity = initial_stock_quantities[symbol]

            if final_quantity != initial_quantity:
                logging.warning(
                    f"Quantity changed for {symbol}: expected {initial_quantity}, got {final_quantity}"
                )

        assert all(
            portfolio.allocated_stocks[symbol].quantity == initial_stock_quantities[symbol]
            for symbol in initial_stock_quantities
        ), "Quantities should not change when prices are stable"

        final_total_value = portfolio.get_total_value().total_value
        tolerance_percentage = Decimal("0.001")

        for symbol, allocated_stock in portfolio.allocated_stocks.items():
            current_allocation_percentage = allocated_stock.total_value / final_total_value
            target_allocation_percentage = allocated_stock.allocation_percentage
            allocation_deviation = abs(
                current_allocation_percentage - target_allocation_percentage
            )

            assert allocation_deviation <= tolerance_percentage, (
                f"Stock {symbol} allocation off: "
                f"expected {target_allocation_percentage:.4%}, got {current_allocation_percentage:.4%}"
            )

        assert broker.buy_operation_count == 0, (
            f"Buy operations called when prices stable. Count: {broker.buy_operation_count}"
        )
        assert broker.sell_operation_count == 0, (
            f"Sell operations called when prices stable. Count: {broker.sell_operation_count}"
        )


class TestHighVolumeRebalancing:

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_rebalancing_with_hundreds_of_random_price_changes(
        self, reset_registries
    ):
        import random

        test_stocks = [
            Stock(symbol="STKA", price=Decimal("100.00")),
            Stock(symbol="STKB", price=Decimal("200.00")),
            Stock(symbol="STKC", price=Decimal("150.00")),
            Stock(symbol="STKD", price=Decimal("300.00")),
            Stock(symbol="STKE", price=Decimal("250.00")),
        ]

        allocation_percentages = [
            Decimal("0.15"),
            Decimal("0.35"),
            Decimal("0.10"),
            Decimal("0.25"),
            Decimal("0.15"),
        ]

        portfolio_config = PortfolioConfig(
            portfolio_name="HighVolumeTest",
            initial_investment=Decimal("50000.00"),
            stocks_to_allocate=[
                StockToAllocate(stock=test_stocks[i], allocation_percentage=allocation_percentages[i])
                for i in range(len(test_stocks))
            ],
            rebalance_lock_ttl_seconds=300,
        )

        initial_market_prices = {
            "STKA": Decimal("100.00"),
            "STKB": Decimal("200.00"),
            "STKC": Decimal("150.00"),
            "STKD": Decimal("300.00"),
            "STKE": Decimal("250.00"),
        }
        test_broker = DummyBroker(market=initial_market_prices, latency_seconds=0.001)

        test_portfolio = Portfolio(
            config=portfolio_config,
            broker=test_broker,
            rebalance_threshold=Decimal("0.01"),
        )

        await test_portfolio.initialize()

        ALLOCATION_TOLERANCE = Decimal("0.001")
        NUMBER_OF_PRICE_CHANGES = 200
        CHECKPOINT_INTERVAL = 50
        MIN_PRICE = Decimal("1.00")
        MAX_PRICE = Decimal("10000.00")
        MAX_PRICE_CHANGE_PERCENT = Decimal("0.20")
        RANDOM_SEED = 42

        random.seed(RANDOM_SEED)
        stock_symbols = [stock.symbol for stock in test_stocks]

        for change_iteration in range(NUMBER_OF_PRICE_CHANGES):
            selected_symbol = random.choice(stock_symbols)

            current_stock_price = test_portfolio.allocated_stocks[selected_symbol].stock.price
            price_variation_percent = Decimal(str(random.uniform(-float(MAX_PRICE_CHANGE_PERCENT), float(MAX_PRICE_CHANGE_PERCENT))))
            updated_price = quantize_money(current_stock_price * (Decimal("1") + price_variation_percent))
            clamped_price = max(MIN_PRICE, min(updated_price, MAX_PRICE))

            test_portfolio.update_allocated_stock_price(selected_symbol, clamped_price)
            await test_portfolio.rebalance()

            if (change_iteration + 1) % CHECKPOINT_INTERVAL == 0:
                current_total_value = test_portfolio.get_total_value().total_value

                for symbol, allocated_stock in test_portfolio.allocated_stocks.items():
                    actual_allocation = allocated_stock.total_value / current_total_value
                    target_allocation = allocated_stock.allocation_percentage
                    allocation_deviation = abs(actual_allocation - target_allocation)

                    assert allocation_deviation <= ALLOCATION_TOLERANCE, (
                        f"Iteration {change_iteration + 1}: Stock {symbol} allocation deviation exceeds tolerance. "
                        f"Target: {target_allocation:.4%}, Actual: {actual_allocation:.4%}"
                    )

        final_portfolio_value = test_portfolio.get_total_value().total_value

        for symbol, allocated_stock in test_portfolio.allocated_stocks.items():
            final_allocation = allocated_stock.total_value / final_portfolio_value
            target_allocation = allocated_stock.allocation_percentage
            final_deviation = abs(final_allocation - target_allocation)

            assert final_deviation <= ALLOCATION_TOLERANCE, (
                f"Final validation failed for {symbol}. "
                f"Target: {target_allocation:.4%}, Actual: {final_allocation:.4%}"
            )

            assert allocated_stock.quantity > Decimal("0"), (
                f"Stock {symbol} has invalid quantity after rebalancing"
            )

        assert test_portfolio.is_locked is False, (
            "Lock should be released after all rebalancing operations complete"
        )

        assert test_broker.buy_operation_count > 0, (
            "Expected buy operations during high-volume rebalancing"
        )
        assert test_broker.sell_operation_count > 0, (
            "Expected sell operations during high-volume rebalancing with price changes"
        )

    @pytest.mark.asyncio
    async def test_rebalancing_with_extreme_price_levels(
        self, reset_registries
    ):
        volatile_stocks = [
            Stock(symbol="VOLA", price=Decimal("100.00")),
            Stock(symbol="VOLB", price=Decimal("100.00")),
            Stock(symbol="VOLC", price=Decimal("100.00")),
        ]

        equal_allocation_config = PortfolioConfig(
            portfolio_name="ExtremePriceLevelsTest",
            initial_investment=Decimal("30000.00"),
            stocks_to_allocate=[
                StockToAllocate(stock=volatile_stocks[0], allocation_percentage=Decimal("0.3333")),
                StockToAllocate(stock=volatile_stocks[1], allocation_percentage=Decimal("0.3333")),
                StockToAllocate(stock=volatile_stocks[2], allocation_percentage=Decimal("0.3334")),
            ],
            rebalance_lock_ttl_seconds=300,
        )

        base_market_prices = {
            "VOLA": Decimal("100.00"),
            "VOLB": Decimal("100.00"),
            "VOLC": Decimal("100.00"),
        }
        volatility_test_broker = DummyBroker(market=base_market_prices, latency_seconds=0.01)

        volatility_test_portfolio = Portfolio(
            config=equal_allocation_config,
            broker=volatility_test_broker,
            rebalance_threshold=Decimal("0.001"),
        )

        await volatility_test_portfolio.initialize()

        ALLOCATION_TOLERANCE = Decimal("0.001")

        price_volatility_scenarios = [
            {"VOLA": Decimal("100.00"), "VOLB": Decimal("500.00"), "VOLC": Decimal("250.00")},
            {"VOLA": Decimal("400.00"), "VOLB": Decimal("150.00"), "VOLC": Decimal("200.00")},
            {"VOLA": Decimal("300.00"), "VOLB": Decimal("350.00"), "VOLC": Decimal("180.00")},
        ]

        for scenario_index, scenario_prices in enumerate(price_volatility_scenarios):
            for symbol, new_price in scenario_prices.items():
                volatility_test_portfolio.update_allocated_stock_price(symbol, new_price)

            await volatility_test_portfolio.rebalance()

            scenario_total_value = volatility_test_portfolio.get_total_value().total_value

            for symbol, allocated_stock in volatility_test_portfolio.allocated_stocks.items():
                actual_allocation = allocated_stock.total_value / scenario_total_value
                target_allocation = allocated_stock.allocation_percentage
                allocation_deviation = abs(actual_allocation - target_allocation)

                assert allocation_deviation <= ALLOCATION_TOLERANCE, (
                    f"Scenario {scenario_index + 1} with prices {scenario_prices}: "
                    f"Stock {symbol} allocation deviation exceeds tolerance. "
                    f"Target: {target_allocation:.4%}, Actual: {actual_allocation:.4%}"
                )

                assert allocated_stock.quantity > Decimal("0"), (
                    f"Stock {symbol} has invalid quantity in scenario {scenario_index + 1}"
                )

        assert volatility_test_portfolio.is_locked is False, "Lock should be released after all extreme price rebalances"
        assert volatility_test_broker.buy_operation_count > 0, "Expected buy operations during extreme price rebalancing"
        assert volatility_test_broker.sell_operation_count > 0, "Expected sell operations during extreme price rebalancing"

class TestRebalanceLockMechanism:

    @pytest.mark.asyncio
    async def test_concurrent_rebalances_are_prevented_by_lock(
        self, sample_portfolio_config: PortfolioConfig, reset_registries
    ):
        market_prices = {
            "AAPL": Decimal("150.00"),
            "MSFT": Decimal("300.00"),
            "GOOG": Decimal("2500.00"),
            "TSLA": Decimal("800.00"),
            "AMZN": Decimal("3200.00"),
        }
        broker = DummyBroker(market=market_prices, latency_seconds=0.1)

        portfolio = Portfolio(
            config=sample_portfolio_config,
            broker=broker,
            rebalance_threshold=Decimal("0.01"),
        )

        await portfolio.initialize()

        new_price = Decimal("200.00")
        for symbol in portfolio.allocated_stocks.keys():
            portfolio.update_allocated_stock_price(symbol, new_price)

        successful_rebalance_count = 0
        blocked_by_lock_count = 0

        async def attempt_rebalance():
            nonlocal successful_rebalance_count, blocked_by_lock_count

            if portfolio.is_locked:
                blocked_by_lock_count += 1
                return

            successful_rebalance_count += 1
            try:
                await portfolio.rebalance()
            except Exception:
                pass

        async def launch_delayed_rebalances():
            await asyncio.sleep(0.05)
            rebalance_tasks = [attempt_rebalance() for _ in range(4)]
            await asyncio.gather(*rebalance_tasks)

        await asyncio.gather(
            attempt_rebalance(),
            launch_delayed_rebalances(),
        )

        assert successful_rebalance_count == 1, (
            f"Expected exactly 1 rebalance to execute, but {successful_rebalance_count} executed"
        )

        assert blocked_by_lock_count > 0, (
            f"Expected some rebalances to be blocked by lock, but got {blocked_by_lock_count}"
        )

        assert portfolio.is_locked is False, (
            "Lock should be released after all rebalance operations complete"
        )

        assert broker.buy_operation_count > 0, (
            "Expected buy operations from the single executed rebalance"
        )

    @pytest.mark.asyncio
    async def test_lock_is_released_after_rebalance_completes(
        self, sample_portfolio_config: PortfolioConfig, reset_registries
    ):
        market_prices = {
            "AAPL": Decimal("150.00"),
            "MSFT": Decimal("300.00"),
            "GOOG": Decimal("2500.00"),
            "TSLA": Decimal("800.00"),
            "AMZN": Decimal("3200.00"),
        }
        broker = DummyBroker(market=market_prices, latency_seconds=0.05)

        portfolio = Portfolio(
            config=sample_portfolio_config,
            broker=broker,
            rebalance_threshold=Decimal("0.01"),
        )

        await portfolio.initialize()

        aapl_quantity_before_first_rebalance = portfolio.allocated_stocks["AAPL"].quantity
        msft_quantity_before_second_rebalance = portfolio.allocated_stocks["MSFT"].quantity

        portfolio.update_allocated_stock_price("AAPL", Decimal("200.00"))
        assert portfolio.is_locked is False, "Lock should not be held before first rebalance"

        await portfolio.rebalance()
        assert portfolio.is_locked is False, "Lock should be released after successful rebalance"
        assert portfolio.lock_age_seconds is None, "Lock timestamp should be cleared after successful rebalance"

        portfolio.update_allocated_stock_price("MSFT", Decimal("400.00"))
        assert portfolio.is_locked is False, "Lock should not be held between rebalances"

        await portfolio.rebalance()
        assert portfolio.is_locked is False, "Lock should be released after second successful rebalance"
        assert portfolio.lock_age_seconds is None, "Lock timestamp should be cleared after second successful rebalance"

        aapl_quantity_after_rebalance = portfolio.allocated_stocks["AAPL"].quantity
        msft_quantity_after_rebalance = portfolio.allocated_stocks["MSFT"].quantity

        assert aapl_quantity_after_rebalance != aapl_quantity_before_first_rebalance, (
            f"First rebalance should have modified AAPL quantity. "
            f"Expected change from {aapl_quantity_before_first_rebalance}, but got {aapl_quantity_after_rebalance}"
        )
        assert msft_quantity_after_rebalance != msft_quantity_before_second_rebalance, (
            f"Second rebalance should have modified MSFT quantity. "
            f"Expected change from {msft_quantity_before_second_rebalance}, but got {msft_quantity_after_rebalance}"
        )

    @pytest.mark.asyncio
    async def test_lock_is_released_after_rebalance_fails(
        self, sample_portfolio_config: PortfolioConfig, reset_registries
    ):
        market_prices = {
            "AAPL": Decimal("150.00"),
            "MSFT": Decimal("300.00"),
            "GOOG": Decimal("2500.00"),
            "TSLA": Decimal("800.00"),
            "AMZN": Decimal("3200.00"),
        }
        broker = DummyBroker(market=market_prices, fail_on_nth_buy=1, latency_seconds=0.05)

        portfolio = Portfolio(
            config=sample_portfolio_config,
            broker=broker,
            rebalance_threshold=Decimal("0.01"),
        )

        await portfolio.initialize()

        trigger_price = Decimal("50.00")
        for symbol in portfolio.allocated_stocks.keys():
            portfolio.update_allocated_stock_price(symbol, trigger_price)

        assert portfolio.is_locked is False, "Lock should not be held before rebalance"

        lock_was_acquired = False
        original_acquire_method = portfolio._can_acquire_rebalance_lock

        def track_lock_acquisition():
            nonlocal lock_was_acquired
            acquired = original_acquire_method()
            if acquired:
                lock_was_acquired = True
            return acquired

        portfolio._can_acquire_rebalance_lock = track_lock_acquisition  # type: ignore[method-assign]

        with pytest.raises(PortfolioError):
            await portfolio.rebalance()

        assert lock_was_acquired, "Lock should have been acquired before rebalance failed"
        assert portfolio.is_locked is False, "Lock should be released after failed rebalance"
        assert portfolio.lock_age_seconds is None, "Lock timestamp should be cleared after failed rebalance"

        broker.reset_counters()
        broker._failure_trigger_threshold = None

        await portfolio.rebalance()
        assert portfolio.is_locked is False, "Lock should be released after recovery rebalance"

        for symbol, allocated_stock in portfolio.allocated_stocks.items():
            stock_quantity = allocated_stock.quantity
            assert stock_quantity >= Decimal("0"), (
                f"Stock {symbol} has invalid quantity after recovery: {stock_quantity}"
            )

    @pytest.mark.asyncio
    async def test_expired_lock_is_acquired_automatically(
        self, sample_portfolio_config: PortfolioConfig, reset_registries
    ):
        from datetime import datetime, timedelta

        short_lock_ttl_config = PortfolioConfig(
            portfolio_name=sample_portfolio_config.portfolio_name,
            initial_investment=sample_portfolio_config.initial_investment,
            stocks_to_allocate=sample_portfolio_config.stocks_to_allocate,
            rebalance_lock_ttl_seconds=1,
        )

        market_prices = {
            "AAPL": Decimal("150.00"),
            "MSFT": Decimal("300.00"),
            "GOOG": Decimal("2500.00"),
            "TSLA": Decimal("800.00"),
            "AMZN": Decimal("3200.00"),
        }
        broker = DummyBroker(market=market_prices, latency_seconds=0.1)

        portfolio = Portfolio(
            config=short_lock_ttl_config,
            broker=broker,
            rebalance_threshold=Decimal("0.01"),
        )

        await portfolio.initialize()

        portfolio._is_rebalancing = True
        portfolio._rebalance_start_time = datetime.now() - timedelta(seconds=2)

        lock_age = portfolio.lock_age_seconds
        assert lock_age is not None and lock_age > portfolio._rebalance_lock_ttl_seconds, (
            "Test setup error: lock should be expired"
        )

        portfolio.update_allocated_stock_price("AAPL", Decimal("999.00"))
        await portfolio.rebalance()

        assert portfolio.is_locked is False, (
            "Lock should be released after rebalance with expired prior lock"
        )
        assert portfolio.lock_age_seconds is None, (
            "Lock timestamp should be cleared after rebalance with expired prior lock"
        )

        final_total_value = portfolio.get_total_value().total_value
        percentage_tolerance = Decimal("0.001")

        for symbol, allocated_stock in portfolio.allocated_stocks.items():
            actual_percentage = allocated_stock.total_value / final_total_value
            expected_percentage = allocated_stock.allocation_percentage
            percentage_difference = abs(actual_percentage - expected_percentage)

            assert percentage_difference <= percentage_tolerance, (
                f"Stock {symbol} allocation off after expired lock rebalance. "
                f"Expected: {expected_percentage:.4%}, Actual: {actual_percentage:.4%}"
            )

        portfolio._is_rebalancing = True
        portfolio._rebalance_start_time = datetime.now()

        await portfolio.rebalance()
        assert portfolio.is_locked is True, (
            "Valid lock should prevent acquisition when already held"
        )

        portfolio._is_rebalancing = False
        portfolio._rebalance_start_time = None


class TestRollbackMechanism:

    @pytest.mark.asyncio
    async def test_rollback_on_partial_rebalance_failure(
        self, reset_registries
    ):
        # Configure initial market prices for all stocks
        initial_market_prices = {
            "AAPL": Decimal("150.00"),
            "MSFT": Decimal("300.00"),
            "GOOG": Decimal("2500.00"),
            "TSLA": Decimal("800.00"),
            "AMZN": Decimal("3200.00"),
        }

        # Create stock instances with initial prices
        stocks = [
            Stock(symbol="AAPL", price=initial_market_prices["AAPL"]),
            Stock(symbol="MSFT", price=initial_market_prices["MSFT"]),
            Stock(symbol="GOOG", price=initial_market_prices["GOOG"]),
            Stock(symbol="TSLA", price=initial_market_prices["TSLA"]),
            Stock(symbol="AMZN", price=initial_market_prices["AMZN"]),
        ]

        # Configure portfolio with equal allocation across all stocks
        portfolio_config = PortfolioConfig(
            portfolio_name="TestPortfolio",
            initial_investment=Decimal("10000.00"),
            stocks_to_allocate=[
                StockToAllocate(stock=stocks[0], allocation_percentage=Decimal("0.20")),
                StockToAllocate(stock=stocks[1], allocation_percentage=Decimal("0.20")),
                StockToAllocate(stock=stocks[2], allocation_percentage=Decimal("0.20")),
                StockToAllocate(stock=stocks[3], allocation_percentage=Decimal("0.20")),
                StockToAllocate(stock=stocks[4], allocation_percentage=Decimal("0.20")),
            ],
            rebalance_lock_ttl_seconds=300,
        )

        # Create broker that will fail on the 3rd buy operation
        broker_with_failure = DummyBroker(
            market=initial_market_prices,
            fail_on_nth_buy=3,
            latency_seconds=0.01
        )

        # Create portfolio instance
        portfolio = Portfolio(
            config=portfolio_config,
            broker=broker_with_failure,
            rebalance_threshold=Decimal("0.01"),
        )

        await portfolio.initialize()

        # Capture initial state before attempting rebalance
        stock_quantities_before_rebalance = {
            symbol: stock.quantity
            for symbol, stock in portfolio.allocated_stocks.items()
        }
        portfolio_value_before_rebalance = portfolio.get_total_value().total_value
        broker_buy_count_before = broker_with_failure.buy_operation_count
        broker_sell_count_before = broker_with_failure.sell_operation_count

        logging.info(f"Initial state: total_value=${portfolio_value_before_rebalance}")

        # Dramatically change all stock prices to trigger rebalancing
        new_stock_price = Decimal("50.00")
        for symbol in portfolio.allocated_stocks.keys():
            portfolio.update_allocated_stock_price(symbol, new_stock_price)

        # Attempt rebalance which should fail and trigger rollback
        with pytest.raises(PortfolioError) as exception_info:
            await portfolio.rebalance()

        # Verify rollback was executed
        exception_message = str(exception_info.value).lower()
        assert "rollback" in exception_message or "rolled back" in exception_message
        assert broker_with_failure.rollback_called

        # Capture state after rollback
        stock_quantities_after_rollback = {
            symbol: stock.quantity
            for symbol, stock in portfolio.allocated_stocks.items()
        }

        # Verify all stock quantities were restored to original values
        for symbol in stock_quantities_before_rebalance.keys():
            quantity_before = stock_quantities_before_rebalance[symbol]
            quantity_after = stock_quantities_after_rollback[symbol]

            assert quantity_after == quantity_before, (
                f"Stock {symbol} quantity NOT restored after rollback: "
                f"expected {quantity_before}, got {quantity_after}, "
                f"delta={quantity_after - quantity_before}"
            )

        # Verify compensating sell operations were executed
        buys_executed = broker_with_failure.buy_operation_count - broker_buy_count_before
        sells_executed = broker_with_failure.sell_operation_count - broker_sell_count_before

        logging.info(f"Rollback: {buys_executed} buys, {sells_executed} sells")

        assert sells_executed > 0, (
            f"Expected compensating sell operations from rollback, "
            f"but got {sells_executed}"
        )

        # Verify portfolio state is consistent after successful rollback
        assert portfolio.is_stale is False, (
            "Portfolio should NOT be in stale state after successful rollback"
        )
        assert portfolio.is_locked is False, (
            "Lock should be released after rollback completes"
        )

    @pytest.mark.asyncio
    async def test_portfolio_state_consistent_after_rollback(
        self, reset_registries
    ):
        # Configure initial market prices for all stocks
        initial_market_prices = {
            "AAPL": Decimal("150.00"),
            "MSFT": Decimal("300.00"),
            "GOOG": Decimal("2500.00"),
            "TSLA": Decimal("800.00"),
            "AMZN": Decimal("3200.00"),
        }

        # Create stock instances with initial prices
        stocks = [
            Stock(symbol="AAPL", price=initial_market_prices["AAPL"]),
            Stock(symbol="MSFT", price=initial_market_prices["MSFT"]),
            Stock(symbol="GOOG", price=initial_market_prices["GOOG"]),
            Stock(symbol="TSLA", price=initial_market_prices["TSLA"]),
            Stock(symbol="AMZN", price=initial_market_prices["AMZN"]),
        ]

        # Configure portfolio with equal allocation across all stocks
        portfolio_config = PortfolioConfig(
            portfolio_name="TestPortfolio",
            initial_investment=Decimal("10000.00"),
            stocks_to_allocate=[
                StockToAllocate(stock=stocks[0], allocation_percentage=Decimal("0.20")),
                StockToAllocate(stock=stocks[1], allocation_percentage=Decimal("0.20")),
                StockToAllocate(stock=stocks[2], allocation_percentage=Decimal("0.20")),
                StockToAllocate(stock=stocks[3], allocation_percentage=Decimal("0.20")),
                StockToAllocate(stock=stocks[4], allocation_percentage=Decimal("0.20")),
            ],
            rebalance_lock_ttl_seconds=300,
        )

        # Create broker that will fail on the 3rd buy operation
        broker_with_failure = DummyBroker(
            market=initial_market_prices,
            fail_on_nth_buy=3,
            latency_seconds=0.01
        )

        # Create portfolio instance
        portfolio = Portfolio(
            config=portfolio_config,
            broker=broker_with_failure,
            rebalance_threshold=Decimal("0.01"),
        )

        await portfolio.initialize()

        # Capture initial state before attempting rebalance
        stock_quantities_before_rebalance = {
            symbol: stock.quantity
            for symbol, stock in portfolio.allocated_stocks.items()
        }
        portfolio_value_info_before = portfolio.get_total_value()
        portfolio_value_before = portfolio_value_info_before.total_value
        portfolio_retail_status_before = portfolio_value_info_before.is_retail

        # Dramatically change all stock prices to trigger rebalancing
        new_stock_price = Decimal("50.00")
        for symbol in portfolio.allocated_stocks.keys():
            portfolio.update_allocated_stock_price(symbol, new_stock_price)

        # Attempt rebalance which should fail and trigger rollback
        with pytest.raises(PortfolioError):
            await portfolio.rebalance()

        # Verify rollback was executed
        assert broker_with_failure.rollback_called

        # Capture state after rollback
        stock_quantities_after_rollback = {
            symbol: stock.quantity
            for symbol, stock in portfolio.allocated_stocks.items()
        }
        portfolio_value_info_after = portfolio.get_total_value()
        portfolio_value_after = portfolio_value_info_after.total_value
        portfolio_retail_status_after = portfolio_value_info_after.is_retail

        # Log any discrepancies in stock quantities
        for symbol in stock_quantities_before_rebalance.keys():
            quantity_before = stock_quantities_before_rebalance[symbol]
            quantity_after = stock_quantities_after_rollback[symbol]

            if quantity_after != quantity_before:
                logging.error(
                    f"Stock {symbol} NOT restored: "
                    f"before={quantity_before}, after={quantity_after}, "
                    f"delta={quantity_after - quantity_before}"
                )

        # Verify all stock quantities were exactly restored
        assert all(
            stock_quantities_after_rollback[symbol] == stock_quantities_before_rebalance[symbol]
            for symbol in stock_quantities_before_rebalance
        ), "All quantities must be exactly restored after rollback"

        # Verify portfolio state consistency after rollback
        assert portfolio_retail_status_after == portfolio_retail_status_before, (
            "Retail status should be unchanged after rollback"
        )
        assert portfolio.is_stale is False, (
            "Portfolio should NOT be in stale state after successful rollback"
        )
        assert portfolio.is_locked is False, (
            "Lock should be released after successful rollback"
        )
        assert portfolio.lock_age_seconds is None, (
            "Lock timestamp should be cleared after successful rollback"
        )
        assert broker_with_failure.sell_operation_count > 0, (
            "Expected compensating sell operations from rollback"
        )

    @pytest.mark.asyncio
    async def test_stale_state_when_rollback_fails(
        self, reset_registries
    ):
        # Configure initial market prices for all stocks
        initial_market_prices = {
            "AAPL": Decimal("150.00"),
            "MSFT": Decimal("300.00"),
            "GOOG": Decimal("2500.00"),
            "TSLA": Decimal("800.00"),
            "AMZN": Decimal("3200.00"),
        }

        # Create stock instances with initial prices
        stocks = [
            Stock(symbol="AAPL", price=initial_market_prices["AAPL"]),
            Stock(symbol="MSFT", price=initial_market_prices["MSFT"]),
            Stock(symbol="GOOG", price=initial_market_prices["GOOG"]),
            Stock(symbol="TSLA", price=initial_market_prices["TSLA"]),
            Stock(symbol="AMZN", price=initial_market_prices["AMZN"]),
        ]

        # Configure portfolio with equal allocation across all stocks
        portfolio_config = PortfolioConfig(
            portfolio_name="TestPortfolio",
            initial_investment=Decimal("10000.00"),
            stocks_to_allocate=[
                StockToAllocate(stock=stocks[0], allocation_percentage=Decimal("0.20")),
                StockToAllocate(stock=stocks[1], allocation_percentage=Decimal("0.20")),
                StockToAllocate(stock=stocks[2], allocation_percentage=Decimal("0.20")),
                StockToAllocate(stock=stocks[3], allocation_percentage=Decimal("0.20")),
                StockToAllocate(stock=stocks[4], allocation_percentage=Decimal("0.20")),
            ],
            rebalance_lock_ttl_seconds=300,
        )

        # Create broker that fails both buy operations and rollback
        broker_with_failing_rollback = FailingRollbackBroker(
            market=initial_market_prices,
            fail_on_nth_buy=3,
            latency_seconds=0.01
        )

        # Create portfolio instance
        portfolio = Portfolio(
            config=portfolio_config,
            broker=broker_with_failing_rollback,
            rebalance_threshold=Decimal("0.01"),
        )

        await portfolio.initialize()

        # Capture initial state before attempting rebalance
        stock_quantities_before_rebalance = {
            symbol: stock.quantity
            for symbol, stock in portfolio.allocated_stocks.items()
        }

        # Dramatically change all stock prices to trigger rebalancing
        new_stock_price = Decimal("50.00")
        for symbol in portfolio.allocated_stocks.keys():
            portfolio.update_allocated_stock_price(symbol, new_stock_price)

        # Attempt rebalance which should fail and trigger failed rollback
        with pytest.raises(PortfolioError) as exception_info:
            await portfolio.rebalance()

        # Verify portfolio entered stale state
        exception_message = str(exception_info.value).lower()
        assert "stale" in exception_message
        assert portfolio.is_stale is True, (
            "Portfolio should be in stale state after failed rollback"
        )
        assert portfolio.is_locked is False, (
            "Rebalance lock should be released even when entering stale state"
        )
        assert portfolio.lock_age_seconds is None, (
            "Lock timestamp should be cleared when entering stale state"
        )

        # Capture state after failed rollback
        stock_quantities_after_failed_rollback = {
            symbol: stock.quantity
            for symbol, stock in portfolio.allocated_stocks.items()
        }

        # Verify quantities remain unchanged after failed rebalance
        assert all(
            stock_quantities_after_failed_rollback[symbol] == stock_quantities_before_rebalance[symbol]
            for symbol in stock_quantities_before_rebalance
        ), "Quantities should be unchanged after failed rebalance"

        # Verify no negative quantities exist
        for symbol, stock in portfolio.allocated_stocks.items():
            assert stock.quantity >= Decimal("0"), (
                f"Stock {symbol} has negative quantity: {stock.quantity}"
            )

        # Verify subsequent rebalance attempts are blocked due to stale state
        with pytest.raises(PortfolioError) as stale_exception:
            await portfolio.rebalance()

        assert "stale" in str(stale_exception.value).lower()
