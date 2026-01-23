import asyncio
import logging
from collections.abc import Awaitable
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from src.broker.broker import (
    BuyStockByAmountRequest,
    BuyStockByQuantityRequest,
    BuyStockResponse,
    SellStockByQuantityRequest,
    SellStockResponse,
)
from src.broker.broker_dtos import BrokerOperation
from src.broker.broker_interface import Broker
from src.config.config import settings
from src.portfolio.errors import PortfolioError, PortfolioInitializationError
from src.portfolio.portfolio_dtos import PortfolioConfig, StockToAllocate
from src.portfolio.portfolio_register import PortfolioRegistry, portfolio_registry
from src.stock.stock import Stock
from src.utils.decimal_utils import quantize_money, quantize_quantity


class PortfolioValue(BaseModel):
    model_config = ConfigDict(frozen=True)

    total_value: Decimal = Field(
        ...,
        gt=0,
        max_digits=settings.shared.money_max_digits,
        decimal_places=settings.shared.money_decimal_precision,
        description="Total value of the portfolio USD",
    )
    is_retail: bool = Field(..., description="Is the portfolio a retail portfolio?")


class AllocatedStock(BaseModel):
    stock: Stock
    allocation_percentage: Decimal = Field(
        ..., gt=0, le=1, description="Percentage of the stock to allocate"
    )
    quantity: Decimal = Field(..., gt=0, description="Quantity of the stock")

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    @property
    def total_value(self) -> Decimal:
        return self.quantity * self.stock.price

    def __repr__(self) -> str:
        return f"""
        AllocatedStock(
            Stock: {self.stock.symbol} : Price: {self.stock.price}

            Percentage: {self.allocation_percentage * 100}%
            Quantity: {self.quantity}
            Total Total Value: {self.total_value}
        )
        """


class Portfolio:
    def __init__(
        self,
        config: PortfolioConfig,
        broker: Broker,
        *,
        registry: PortfolioRegistry | None = None,
        retail_threshold_usd: int | None = None,
        rebalance_threshold: Decimal | None = None,
    ):
        """Initialize a Portfolio with configuration and broker.

        Args:
            config: Portfolio configuration with name, investment, and stocks
            broker: Broker instance for executing trades
            registry: Portfolio registry for registration (default: global registry)
            retail_threshold_usd: Threshold for retail classification (default: 25000)
            rebalance_threshold: Minimum quantity difference to trigger rebalancing (default: 0.00)
        """
        self._portfolio_name = config.portfolio_name
        self._initial_investment = config.initial_investment
        self._stock_to_allocate: dict[str, StockToAllocate] = {}
        self._allocated_stocks: dict[str, AllocatedStock] = {}
        self._broker = broker
        self._stale: bool = False
        self._registry = registry

        self._retail_threshold_usd = (
            retail_threshold_usd if retail_threshold_usd is not None else 25000
        )
        self._rebalance_threshold = (
            rebalance_threshold if rebalance_threshold is not None else Decimal("0.00")
        )

        # Thread-safe rebalance lock with TTL tracking
        self._rebalance_lock = asyncio.Lock()
        self._is_rebalancing = False
        self._rebalance_start_time: datetime | None = None
        self._rebalance_lock_ttl_seconds: int = config.rebalance_lock_ttl_seconds

        self._set_stock_to_allocate(config.stocks_to_allocate)

        active_registry = (
            self._registry if self._registry is not None else portfolio_registry
        )
        active_registry.add(self)

    @property
    def portfolio_name(self) -> str:
        return self._portfolio_name

    @property
    def allocated_stocks(self) -> dict[str, AllocatedStock]:
        return self._allocated_stocks

    @property
    def is_locked(self) -> bool:
        """Check if portfolio is currently locked (rebalancing in progress)."""
        return self._is_rebalancing

    @property
    def is_stale(self) -> bool:
        """Check if portfolio is in stale state."""
        return self._stale

    @property
    def lock_age_seconds(self) -> float | None:
        """Get the age of the current lock in seconds, or None if not locked."""
        if self._rebalance_start_time is None:
            return None
        return (datetime.now() - self._rebalance_start_time).total_seconds()

    def get_total_value(self) -> PortfolioValue:
        total_value = sum(
            (stock.total_value for stock in self._allocated_stocks.values()), Decimal(0)
        )
        total_value = quantize_money(total_value)
        is_retail = total_value < self._retail_threshold_usd

        return PortfolioValue(total_value=total_value, is_retail=is_retail)

    def _set_stock_to_allocate(self, stocks_to_allocate: list[StockToAllocate]) -> None:
        for stock in stocks_to_allocate:
            self._stock_to_allocate[stock.stock.symbol] = stock

    def _check_stale_state(self) -> None:
        """Raise error if portfolio is in stale state."""
        if self._stale:
            logging.warning(
                f"Rebalance rejected for '{self._portfolio_name}': "
                "portfolio is in stale state. Manual recovery required."
            )
            raise PortfolioError(
                f"Portfolio '{self._portfolio_name}' is in stale state. "
                "Manual recovery required. Call clear_stale_state() after verification."
            )

    def set_stale_state(self) -> None:
        """Manually set the stale state."""
        self._stale = True
        logging.info(f"Alert: Stale state set for '{self._portfolio_name}'")

    def clear_stale_state(self) -> None:
        """Manually clear the stale state."""
        self._stale = False
        logging.info(f"Alert: Stale state cleared for '{self._portfolio_name}'")

    def _has_lock_expired(self) -> bool:
        """Check if the current rebalance lock has exceeded its TTL.

        Returns True if the lock age exceeds the configured TTL.
        """
        if self._rebalance_start_time is None:
            return False

        lock_age = datetime.now() - self._rebalance_start_time
        return lock_age.total_seconds() > self._rebalance_lock_ttl_seconds

    def _can_acquire_rebalance_lock(self) -> bool:
        """Check if the rebalance lock can be acquired.

        Returns True if:
        - No rebalance is currently in progress, OR
        - The current lock has expired (TTL exceeded)

        If the lock has expired, it will be cleaned up automatically.

        This method is used by tests to verify lock behavior.
        """
        if not self._is_rebalancing:
            return True

        if self._has_lock_expired():
            logging.warning(
                f"Rebalance lock for '{self._portfolio_name}' has expired. Cleaning up."
            )
            self._is_rebalancing = False
            self._rebalance_start_time = None
            return True

        return False

    async def initialize(self) -> None:
        """
        Initialize portfolio with batch support and automatic rollback.

        Raises:
            PortfolioInitializationError: If initialization fails
            PortfolioError: If portfolio is in stale state
        """
        self._check_stale_state()

        async with self._rebalance_lock:
            self._rebalance_start_time = datetime.now()

            try:
                batch_uuid = uuid4()

                tasks_by_symbol: dict[str, Awaitable[BuyStockResponse]] = {}
                for stock in self._stock_to_allocate.values():
                    amount = quantize_money(
                        self._initial_investment * stock.allocation_percentage
                    )
                    request = BuyStockByAmountRequest(
                        symbol=stock.stock.symbol,
                        amount=amount,
                        batch_uuid=batch_uuid,
                    )
                    tasks_by_symbol[request.symbol] = self._buy_stock_by_amount(request)

                results_list: list[BrokerOperation | Exception] = await asyncio.gather(
                    *tasks_by_symbol.values(), return_exceptions=True
                )

                failed_operations = []
                failed_operations.extend(
                    f"{symbol}: {result}"
                    for symbol, result in zip(tasks_by_symbol, results_list, strict=True)
                    if isinstance(result, Exception)
                )

                if failed_operations:
                    rollback_success = await self._broker.batch_rollback(batch_uuid)

                    if not rollback_success:
                        self.set_stale_state()
                        raise PortfolioInitializationError(
                            "Initialization failed. Rollback also failed. Portfolio is in stale state.",
                            failed_operations=failed_operations,
                        )

                    raise PortfolioInitializationError(
                        f"All {len(failed_operations)} operations failed: "
                        + "; ".join(failed_operations),
                        failed_operations=failed_operations,
                    )

            finally:
                self._rebalance_start_time = None

    def update_allocated_stock_price(self, symbol: str, price: Decimal) -> None:
        self._allocated_stocks[symbol].stock.current_price(price)

    def _get_balance_operations_batch(
        self,
        batch_uuid,
    ) -> tuple[list[Awaitable[BuyStockResponse]], list[Awaitable[SellStockResponse]]]:
        """Get balance operations with batch UUID included."""

        broker = self._broker
        portfolio_total_value = self.get_total_value().total_value

        buy_operations_list: list[Awaitable[BuyStockResponse]] = []
        sell_operations_list: list[Awaitable[SellStockResponse]] = []

        for allocated_stock in self._allocated_stocks.values():
            new_objective_total_value = (
                portfolio_total_value * allocated_stock.allocation_percentage
            )
            new_objective_quantity = quantize_quantity(
                new_objective_total_value / allocated_stock.stock.price
            )

            quantity_difference = new_objective_quantity - allocated_stock.quantity

            need_to_rebalance = abs(quantity_difference) > self._rebalance_threshold
            if not need_to_rebalance:
                continue

            if quantity_difference > 0:  # Need to buy
                buy_operations_list.append(
                    broker.buy_stock_by_quantity(
                        BuyStockByQuantityRequest(
                            symbol=allocated_stock.stock.symbol,
                            quantity=quantize_quantity(abs(quantity_difference)),
                            batch_uuid=batch_uuid,
                        )
                    )
                )
            elif quantity_difference < 0:  # Need to sell
                sell_operations_list.append(
                    broker.sell_stock_by_quantity(
                        SellStockByQuantityRequest(
                            symbol=allocated_stock.stock.symbol,
                            quantity=quantize_quantity(abs(quantity_difference)),
                            batch_uuid=batch_uuid,
                        )
                    )
                )

        return buy_operations_list, sell_operations_list

    async def rebalance(self) -> None:
        self._check_stale_state()

        if not self._can_acquire_rebalance_lock():
            logging.warning(
                f"Rebalance rejected for '{self._portfolio_name}': "
                "another rebalance is already in progress"
            )
            return

        async with self._rebalance_lock:
            self._is_rebalancing = True
            self._rebalance_start_time = datetime.now()
            logging.info(f"Rebalance lock acquired for '{self._portfolio_name}'")

            try:
                batch_uuid = uuid4()
                buy_operations_list, sell_operations_list = (
                    self._get_balance_operations_batch(batch_uuid)
                )

                buy_results: list[BuyStockResponse | Exception] = []
                sell_results: list[SellStockResponse | Exception] = []

                if buy_operations_list:
                    buy_results = await asyncio.gather(
                        *buy_operations_list, return_exceptions=True
                    )

                if sell_operations_list:
                    sell_results = await asyncio.gather(
                        *sell_operations_list, return_exceptions=True
                    )

                buy_failures = [
                    failure for failure in buy_results if isinstance(failure, Exception)
                ]
                sell_failures = [
                    failure for failure in sell_results if isinstance(failure, Exception)
                ]
                failures = buy_failures + sell_failures

                if not failures:
                    for response in buy_results:
                        if isinstance(response, BuyStockResponse):
                            self._allocated_stocks[
                                response.symbol
                            ].quantity += response.quantity
                        logging.info(
                            f"Buy operation to balance the {self.portfolio_name} portfolio result: {response.symbol} : Q: {response.quantity}"
                        )

                    for response in sell_results:
                        if isinstance(response, SellStockResponse):
                            self._allocated_stocks[
                                response.symbol
                            ].quantity -= response.quantity
                        logging.info(
                            f"Sell operation to balance the {self.portfolio_name} portfolio result: {response.symbol} : Q: {response.quantity}"
                        )

                    return

                has_successful_operations = any(
                    isinstance(result, (BuyStockResponse, SellStockResponse))
                    for result in (*buy_results, *sell_results)
                )

                if not has_successful_operations:
                    raise PortfolioError(
                        f"Rebalancing failed: {'; '.join(str(e) for e in failures)}"
                    )

                rollback_success = await self._broker.batch_rollback(batch_uuid)

                if rollback_success:
                    raise PortfolioError(
                        "Rebalancing failed. Rolled back partial executions in broker."
                    )

                self.set_stale_state()
                raise PortfolioError(
                    "Rebalancing failed. Rollback also failed. Stale state."
                )

            finally:
                self._is_rebalancing = False
                self._rebalance_start_time = None
                logging.info(f"Rebalance lock released for '{self._portfolio_name}'")

    async def _buy_stock(
        self, buy_stock_by_quantity_request: BuyStockByQuantityRequest
    ) -> None:
        self._check_stale_state()
        buy_stock_by_quantity_response: BuyStockResponse = (
            await self._broker.buy_stock_by_quantity(buy_stock_by_quantity_request)
        )

        self._allocated_stocks[
            buy_stock_by_quantity_response.symbol
        ].quantity += buy_stock_by_quantity_response.quantity

    async def _sell_stock(
        self, sell_stock_by_quantity_request: SellStockByQuantityRequest
    ) -> None:
        self._check_stale_state()
        sell_stock_by_quantity_response: SellStockResponse = (
            await self._broker.sell_stock_by_quantity(sell_stock_by_quantity_request)
        )

        self._allocated_stocks[
            sell_stock_by_quantity_response.symbol
        ].quantity -= sell_stock_by_quantity_response.quantity

    async def _buy_stock_by_amount(
        self, buy_stock_by_amount_request: BuyStockByAmountRequest
    ) -> None:
        """Buy stock by amount and update the portfolio state."""
        response = await self._broker.buy_stock_by_amount(buy_stock_by_amount_request)
        self._allocated_stocks[response.symbol] = AllocatedStock(
            stock=Stock(symbol=response.symbol, price=response.price),
            allocation_percentage=self._stock_to_allocate[
                response.symbol
            ].allocation_percentage,
            quantity=response.quantity,
        )

    def __repr__(self) -> str:
        return f"""
        Portfolio(
            portfolio_name={self._portfolio_name},
            initial_investment={self._initial_investment},
            allocated_stocks={self._allocated_stocks}
        )
        """
