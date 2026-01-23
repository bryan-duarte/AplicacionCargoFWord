"""Data Transfer Objects (DTOs) for Portfolio configuration and instantiation."""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from src.config.config import settings
from src.stock.stock import Stock

_DEFAULT_MINIMUM_INVESTMENT_USD = 1
_EXPECTED_ALLOCATION_SUM = Decimal("1.0")
_ROUNDING_TOLERANCE = Decimal("0.0001")


class StockToAllocate(BaseModel):
    stock: Stock = Field(
        ..., description="Stock entity with symbol and price"
    )
    allocation_percentage: Decimal = Field(
        ...,
        gt=0,
        le=Decimal("1"),
        max_digits=settings.shared.percentage_max_digits,
        decimal_places=settings.shared.percentage_decimal_precision,
        description="Allocation percentage as decimal (0.0001 to 1.0000, where 1.0 = 100%)",
    )

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        frozen=True,
    )

    @field_validator("stock")
    @classmethod
    def validate_stock_not_none(cls, stock: Stock) -> Stock:
        if stock is None:
            raise ValueError("Stock cannot be None")
        if not stock.symbol or not stock.symbol.strip():
            raise ValueError("Stock symbol cannot be empty or None")
        return stock

    @field_validator("allocation_percentage")
    @classmethod
    def validate_allocation_percentage_not_zero(cls, allocation_percentage: Decimal) -> Decimal:
        if allocation_percentage <= 0:
            raise ValueError(
                f"Allocation percentage must be greater than 0. Got: {allocation_percentage}"
            )
        return allocation_percentage


class PortfolioConfig(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        arbitrary_types_allowed=True,
    )

    portfolio_name: str = Field(
        ..., min_length=1, max_length=100, description="Identifying name of this portfolio"
    )

    initial_investment: Decimal = Field(
        ...,
        gt=Decimal("0"),
        ge=Decimal(str(_DEFAULT_MINIMUM_INVESTMENT_USD)),
        le=settings.shared.money_max_value,
        max_digits=settings.shared.money_max_digits,
        decimal_places=settings.shared.money_decimal_precision,
        description="Initial investment amount in USD (must be between minimum and broker limits)",
    )

    stocks_to_allocate: list[StockToAllocate] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="List of stocks with their allocation percentages (must sum to 100%)",
    )

    rebalance_lock_ttl_seconds: int = Field(
        default=21600,
        gt=0,
        le=86400,
        description="TTL for rebalance lock in seconds (default: 21600 = 6 hours, max: 86400 = 24 hours)",
    )

    @field_validator("portfolio_name")
    @classmethod
    def validate_portfolio_name_not_empty(cls, portfolio_name: str) -> str:
        if portfolio_name is None:
            raise ValueError("Portfolio name cannot be None")
        stripped_name = portfolio_name.strip()
        if not stripped_name:
            raise ValueError("Portfolio name cannot be empty or whitespace only")
        return stripped_name

    @field_validator("initial_investment")
    @classmethod
    def validate_initial_investment_positive(cls, initial_investment: Decimal) -> Decimal:
        if initial_investment is None:
            raise ValueError("Initial investment cannot be None")
        if initial_investment <= 0:
            raise ValueError(
                f"Initial investment must be greater than 0. Got: {initial_investment}"
            )
        if initial_investment < Decimal(str(_DEFAULT_MINIMUM_INVESTMENT_USD)):
            raise ValueError(
                f"Initial investment must be at least ${_DEFAULT_MINIMUM_INVESTMENT_USD} USD. Got: ${initial_investment}"
            )
        return initial_investment

    @field_validator("stocks_to_allocate")
    @classmethod
    def validate_stocks_not_empty(cls, stocks: list[StockToAllocate]) -> list[StockToAllocate]:
        if stocks is None:
            raise ValueError("Stocks to allocate cannot be None")
        if not stocks:
            raise ValueError("Portfolio must contain at least one stock to allocate")
        return stocks

    @field_validator("stocks_to_allocate")
    @classmethod
    def validate_unique_stock_symbols(
        cls, allocations: list[StockToAllocate]
    ) -> list[StockToAllocate]:
        if allocations is None:
            raise ValueError("Stock allocations cannot be None")

        stock_symbols = [allocation.stock.symbol for allocation in allocations]
        unique_stock_symbols = set(stock_symbols)

        has_duplicates = len(stock_symbols) != len(unique_stock_symbols)
        if has_duplicates:
            duplicates = [symbol for symbol in stock_symbols if stock_symbols.count(symbol) > 1]
            unique_duplicates = set(duplicates)
            raise ValueError(
                f"Portfolio cannot contain duplicate stock symbols. "
                f"Found duplicates: {', '.join(unique_duplicates)}"
            )

        return allocations

    @model_validator(mode="after")
    def validate_allocation_percentages_sum_to_100_percent(self) -> "PortfolioConfig":
        if self.stocks_to_allocate is None or not self.stocks_to_allocate:
            raise ValueError("Stocks to allocate cannot be None or empty")

        actual_allocation_sum = Decimal("0")
        for allocation in self.stocks_to_allocate:
            if allocation.allocation_percentage is None:
                raise ValueError("Allocation percentage cannot be None")
            if allocation.allocation_percentage <= 0:
                raise ValueError(
                    f"Allocation percentage must be greater than 0. "
                    f"Stock '{allocation.stock.symbol}' has allocation: {allocation.allocation_percentage}"
                )
            actual_allocation_sum += allocation.allocation_percentage

        allocation_difference = actual_allocation_sum - _EXPECTED_ALLOCATION_SUM
        absolute_difference = abs(allocation_difference)

        actual_sum_as_percentage = actual_allocation_sum * Decimal("100")
        difference_as_percentage = absolute_difference * Decimal("100")

        if absolute_difference <= _ROUNDING_TOLERANCE:
            if absolute_difference > Decimal("0"):
                import logging

                largest_allocation_index = max(
                    range(len(self.stocks_to_allocate)),
                    key=lambda i: self.stocks_to_allocate[i].allocation_percentage,
                )
                largest_allocation = self.stocks_to_allocate[largest_allocation_index]
                original_percentage = largest_allocation.allocation_percentage
                adjusted_percentage = largest_allocation.allocation_percentage - allocation_difference

                adjusted_percentage = adjusted_percentage.quantize(
                    Decimal("0.0001")
                )

                logging.warning(
                    f"Allocation percentages adjusted by {difference_as_percentage}% "
                    f"to sum exactly to 100%. "
                    f"'{largest_allocation.stock.symbol}' adjusted from "
                    f"{original_percentage * Decimal('100')}% to {adjusted_percentage * Decimal('100')}%"
                )

                adjusted_stocks = list(self.stocks_to_allocate)
                adjusted_stock = StockToAllocate(
                    stock=largest_allocation.stock,
                    allocation_percentage=adjusted_percentage,
                )
                adjusted_stocks[largest_allocation_index] = adjusted_stock

                object.__setattr__(
                    self, "stocks_to_allocate", tuple(adjusted_stocks)
                )

            return self

        raise ValueError(
            f"Stock allocation percentages must sum to 100%. "
            f"Current sum: {actual_sum_as_percentage}%. "
            f"Difference: {difference_as_percentage}%. "
            f"Please adjust allocations to sum exactly to 100%."
        )

    @model_validator(mode="after")
    def validate_minimum_number_of_stocks(self) -> "PortfolioConfig":
        if self.stocks_to_allocate is None:
            raise ValueError("Stocks to allocate cannot be None")

        num_stocks = len(self.stocks_to_allocate)
        if num_stocks < 1:
            raise ValueError(
                f"Portfolio must contain at least 1 stock. Current: {num_stocks}"
            )

        if num_stocks < 2:
            from warnings import warn

            warn(
                f"Portfolio with only {num_stocks} stock(s) may not provide adequate diversification. "
                "Consider adding more stocks."
            )

        return self
