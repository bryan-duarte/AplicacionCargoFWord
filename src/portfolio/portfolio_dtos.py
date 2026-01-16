"""Data Transfer Objects (DTOs) for Portfolio configuration and instantiation."""
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
from src.config.config import settings
from src.stock.stock import Stock

_DEFAULT_MINIMUM_INVESTMENT_USD = 1


class StockToAllocate(BaseModel):
    stock: Stock
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


class PortfolioConfig(BaseModel):

    model_config = ConfigDict(
        frozen=True,
        arbitrary_types_allowed=True,
    )

    portfolio_name: str = Field(
        ...,
        min_length=1,
        description="Identifying name of this portfolio"
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
        description="List of stocks with their allocation percentages (must sum to 100%)",
    )

    rebalance_lock_ttl_seconds: int = Field(
        default=21600,
        gt=0,
        description="TTL for rebalance lock in seconds (default: 21600 = 6 hours)",
    )

    @field_validator('stocks_to_allocate')
    @classmethod
    def validate_unique_stock_symbols(cls, allocations: list[StockToAllocate]) -> list[StockToAllocate]:

        stock_symbols = [allocation.stock.symbol for allocation in allocations]
        unique_stock_symbols = set(stock_symbols)

        has_duplicates = len(stock_symbols) != len(unique_stock_symbols)
        if has_duplicates:
            raise ValueError(
                f"Portfolio cannot contain duplicate stock symbols. "
                f"Found duplicates in: {', '.join(unique_stock_symbols)}"
            )

        return allocations

    @model_validator(mode='after')
    def validate_allocation_percentages_sum_to_100_percent(self) -> 'PortfolioConfig':

        expected_allocation_sum = settings.shared.percentage_expected_sum
        allowed_tolerance = settings.shared.percentage_tolerance

        actual_allocation_sum = Decimal("0")
        for allocation in self.stocks_to_allocate:
            actual_allocation_sum += allocation.allocation_percentage

        allocation_difference_from_100_percent = abs(actual_allocation_sum - expected_allocation_sum)
        exceeds_tolerance = allocation_difference_from_100_percent >= allowed_tolerance

        if exceeds_tolerance:
            actual_sum_as_percentage = actual_allocation_sum * Decimal("100")
            expected_sum_as_percentage = expected_allocation_sum * Decimal("100")
            raise ValueError(
                f"Stock allocation percentages must sum to {expected_sum_as_percentage}%. "
                f"Current sum: {actual_sum_as_percentage}% "
                f"(difference: {allocation_difference_from_100_percent * Decimal('100')}%)"
            )

        return self
