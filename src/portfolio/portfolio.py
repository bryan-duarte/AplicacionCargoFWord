from decimal import Decimal
from typing import Awaitable, Union
from uuid import uuid4
import logging
import asyncio
from pydantic import BaseModel, ConfigDict, Field
from src.broker.broker import (
    BuyStockByAmountRequest,
    BuyStockByQuantityRequest,
    SellStockByQuantityRequest,
    BuyStockResponse,
    SellStockResponse,
)
from src.broker.broker_dtos import BrokerOperation
from src.broker.broker_interface import Broker
from src.config.config import settings
from src.portfolio.errors import PortfolioError, PortfolioInitializationError
from typing import Optional
from src.portfolio.portfolio_dtos import PortfolioConfig, StockToAllocate
from src.portfolio.portfolio_register import portfolio_registry
from src.stock.stock import Stock
from src.utils.decimal_utils import quantize_money


class PortfolioValue(BaseModel):
    model_config = ConfigDict(frozen=True)

    total_value: Decimal = Field(
        ...,
        gt=0,
        max_digits=settings.shared.money_max_digits,
        decimal_places=settings.shared.money_decimal_precision,
        description="Total value of the portfolio USD"
    )
    is_retail: bool = Field(
        ...,
        description="Is the portfolio a retail portfolio?"
    )


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
        retail_threshold_usd: Optional[int] = None,
        rebalance_threshold: Optional[Decimal] = None,
    ):
        """Initialize a Portfolio with configuration and broker.

        Args:
            config: Portfolio configuration with name, investment, and stocks
            broker: Broker instance for executing trades
            retail_threshold_usd: Threshold for retail classification (default: 25000)
            rebalance_threshold: Minimum quantity difference to trigger rebalancing (default: 0.00)
        """
        self._portfolio_name = config.portfolio_name
        self._initial_investment = config.initial_investment
        self._stock_to_allocate: dict[str, StockToAllocate] = {}
        self._allocated_stocks: dict[str, AllocatedStock] = {}
        self._broker = broker
        self._stale: bool = False

        self._retail_threshold_usd = retail_threshold_usd if retail_threshold_usd is not None else 25000
        self._rebalance_threshold = rebalance_threshold if rebalance_threshold is not None else Decimal("0.00")

        self._set_stock_to_allocate(config.stocks_to_allocate)
        portfolio_registry.add(self)

    @property
    def portfolio_name(self) -> str:
        return self._portfolio_name

    @property
    def allocated_stocks(self) -> dict[str, AllocatedStock]:
        return self._allocated_stocks

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

    async def initialize(self) -> None:
        """
        Initialize portfolio with batch support and automatic rollback.

        Raises:
            PortfolioInitializationError: If initialization fails
            PortfolioError: If portfolio is in stale state
        """
        self._check_stale_state()
        batch_uuid = uuid4()

        tasks_by_symbol: dict[str, Awaitable[BuyStockResponse]] = {}
        for stock in self._stock_to_allocate.values():
            request = BuyStockByAmountRequest(
                symbol=stock.stock.symbol,
                amount=self._initial_investment * stock.allocation_percentage,
                batch_uuid=batch_uuid,
            )
            tasks_by_symbol[request.symbol] = self._buy_stock_by_amount(request)

        results_list: list[Union[BrokerOperation, Exception]] = await asyncio.gather(
            *tasks_by_symbol.values(), return_exceptions=True
        )

        failed_operations = []
        failed_operations.extend(
            f"{symbol}: {result}"
            for symbol, result in zip(tasks_by_symbol, results_list)
            if isinstance(result, Exception)
        )

        if failed_operations:
            rollback_success = await self._broker.batch_rollback(batch_uuid)

            if not rollback_success:
                self.set_stale_state()
                raise PortfolioInitializationError(
                        f"Initialization failed. Rollback also failed. Portfolio is in stale state.",
                        failed_operations=failed_operations,
                    )

            raise PortfolioInitializationError(
                f"All {len(failed_operations)} operations failed: " + "; ".join(failed_operations),
                failed_operations=failed_operations,
            )

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
            new_objective_quantity = (
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
                            quantity=abs(quantity_difference),
                            batch_uuid=batch_uuid,
                        )
                    )
                )
            elif quantity_difference < 0:  # Need to sell
                sell_operations_list.append(
                    broker.sell_stock_by_quantity(
                        SellStockByQuantityRequest(
                            symbol=allocated_stock.stock.symbol,
                            quantity=abs(quantity_difference),
                            batch_uuid=batch_uuid,
                        )
                    )
                )

        return buy_operations_list, sell_operations_list

    async def rebalance(self) -> None:
        """Rebalance portfolio with batch support and automatic rollback."""
        self._check_stale_state()

        batch_uuid = uuid4()

        buy_operations_list, sell_operations_list = self._get_balance_operations_batch(batch_uuid)

        buy_results: list[Union[BuyStockResponse, Exception]] = []
        sell_results: list[Union[SellStockResponse, Exception]] = []
        
        if buy_operations_list:
            buy_results = await asyncio.gather(*buy_operations_list, return_exceptions=True)
            
            for response in buy_results:
                if isinstance(response, BuyStockResponse):
                    self._allocated_stocks[response.symbol].quantity += response.quantity

            buy_failures = [
                failure
                for failure in buy_results
                if isinstance(failure, Exception)
            ]

        if sell_operations_list:
            sell_results = await asyncio.gather(*sell_operations_list, return_exceptions=True)
            
            for response in sell_results:
                if isinstance(response, SellStockResponse):
                    self._allocated_stocks[response.symbol].quantity -= response.quantity

            sell_failures = [
                failure
                for failure in sell_results
                if isinstance(failure, Exception)
            ]

        failures = buy_failures + sell_failures

        if failures:
            has_successful_operations = any(
                isinstance(result, (BuyStockResponse, SellStockResponse))
                for result in (*buy_results, *sell_results)
            )

            if has_successful_operations:
                rollback_success = await self._broker.batch_rollback(batch_uuid)

                if not rollback_success:
                    self.set_stale_state()
                    raise PortfolioError("Rebalancing failed. Rollback also failed. Stale state.")

                raise PortfolioError(
                    "Rebalancing failed. Successfully rolled back prior successful operations."
                )

            raise PortfolioError(f"Rebalancing failed: {'; '.join(str(e) for e in failures)}")

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
            allocation_percentage=self._stock_to_allocate[response.symbol].allocation_percentage,
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
