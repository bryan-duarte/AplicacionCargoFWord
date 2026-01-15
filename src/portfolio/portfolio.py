from functools import partial
from src.stock.stock import Stock
from pydantic import BaseModel, ConfigDict, Field
from src.broker.broker import (
    BuyStockByAmountRequest,
    BuyStockByQuantityRequest,
    SellStockByQuantityRequest,
    BuyStockResponse,
    SellStockResponse,
)
from src.broker.broker_interface import Broker
import asyncio
from typing import Awaitable
from src.config.config import settings
from src.portfolio.portfolio_register import portfolio_registry
from src.portfolio.errors import PortfolioInitializationError
from src.portfolio.portfolio_dtos import PortfolioConfig, StockToAllocate
from src.utils.decimal_utils import quantize_money
from decimal import Decimal

__all__ = ['Portfolio', 'PortfolioValue', 'AllocatedStock', 'StockToAllocate']


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
    ):
        self._portfolio_name = config.portfolio_name
        self._initial_investment = config.initial_investment
        self._stock_to_allocate: dict[str, StockToAllocate] = {}
        self._allocated_stocks: dict[str, AllocatedStock] = {}
        self._broker = broker

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
        is_retail = total_value < settings.portfolio.retail_threshold_usd

        return PortfolioValue(total_value=total_value, is_retail=is_retail)

    def _set_stock_to_allocate(self, stocks_to_allocate: list[StockToAllocate]) -> None:
        for stock in stocks_to_allocate:
            self._stock_to_allocate[stock.stock.symbol] = stock

    async def initialize(self) -> None:
        """
        Initialize portfolio by buying all allocated stocks with retry logic.

        Implements idempotency by verifying operation status and retrying failed
        operations. Uses exponential backoff for retries. Fails completely if any
        operation cannot succeed after all retry attempts (atomic operation).

        Raises:
            PortfolioInitializationError: If any stock purchase fails permanently
        """
        buy_tasks: list[Awaitable[BuyStockResponse]] = []
        for stock in self._stock_to_allocate.values():
            buy_tasks.append(
                self._buy_stock_by_amount(
                    BuyStockByAmountRequest(
                        symbol=stock.stock.symbol,
                        amount=self._initial_investment * stock.allocation_percentage,
                    )
                )
            )

        results = await asyncio.gather(*buy_tasks, return_exceptions=True)

        failed_operations = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                symbol = list(self._stock_to_allocate.keys())[i]
                failed_operations.append(f"{symbol}: {str(result)}")

        if failed_operations:
            raise PortfolioInitializationError(
                f"Portfolio initialization failed. {len(failed_operations)} operations failed: "
                + "; ".join(failed_operations),
                failed_operations=failed_operations
            )

    def update_allocated_stock_price(self, symbol: str, price: Decimal) -> None:
        self._allocated_stocks[symbol].stock.current_price(price)

    def _get_balance_operations(
        self,
    ) -> tuple[list[Awaitable[BuyStockResponse]], list[Awaitable[SellStockResponse]]]:
        portfolio_total_value = self.get_total_value().total_value

        buy_operations_list: list[Awaitable[BuyStockResponse]] = []
        sell_operations_list: list[Awaitable[SellStockResponse]] = []

        broker = self._broker

        for allocated_stock in self._allocated_stocks.values():
            new_objective_total_value = (
                portfolio_total_value * allocated_stock.allocation_percentage
            )
            new_objective_quantity = (
                new_objective_total_value / allocated_stock.stock.price
            )

            quantity_difference = new_objective_quantity - allocated_stock.quantity

            need_to_rebalance = abs(quantity_difference) > settings.portfolio.rebalance_threshold
            if not need_to_rebalance:
                continue

            need_to_buy = quantity_difference > 0
            if need_to_buy:
                buy_operations_list.append(
                    broker.buy_stock_by_quantity(
                        BuyStockByQuantityRequest(
                            symbol=allocated_stock.stock.symbol,
                            quantity=abs(quantity_difference),
                        )
                    )
                )

            need_to_sell = quantity_difference < 0
            if need_to_sell:
                sell_operations_list.append(
                    broker.sell_stock_by_quantity(
                        SellStockByQuantityRequest(
                            symbol=allocated_stock.stock.symbol,
                            quantity=abs(quantity_difference),
                        )
                    )
                )
        return buy_operations_list, sell_operations_list

    async def rebalance(self) -> None:
        buy_operations_list, sell_operations_list = self._get_balance_operations()

        if buy_operations_list:
            buy_executed_operations: list[BuyStockResponse] = await asyncio.gather(
                *buy_operations_list
            )
            for response in buy_executed_operations:
                self._allocated_stocks[response.symbol].quantity += response.quantity

        if sell_operations_list:
            sell_executed_operations: list[SellStockResponse] = await asyncio.gather(
                *sell_operations_list
            )
            for response in sell_executed_operations:
                self._allocated_stocks[response.symbol].quantity -= response.quantity

    async def _buy_stock(
        self, buy_stock_by_quantity_request: BuyStockByQuantityRequest
    ) -> None:
        buy_stock_by_quantity_response: BuyStockResponse = (
            await self._broker.buy_stock_by_quantity(buy_stock_by_quantity_request)
        )

        self._allocated_stocks[
            buy_stock_by_quantity_response.symbol
        ].quantity += buy_stock_by_quantity_response.quantity

    async def _sell_stock(
        self, sell_stock_by_quantity_request: SellStockByQuantityRequest
    ) -> None:
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
