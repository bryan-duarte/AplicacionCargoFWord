"""Application configuration settings.

This module contains only settings that are used across multiple modules.
Settings specific to a single module are defined as instance attributes with default values.
"""

from decimal import Decimal, getcontext

from pydantic import BaseModel, ConfigDict, Field

getcontext().prec = 28


class SharedSettings(BaseModel):
    """Shared settings between modules.

    These settings are used in multiple modules across the application.
    """

    model_config = ConfigDict(frozen=True)

    money_decimal_precision: int = Field(
        default=2, description="Decimal precision for USD amounts"
    )
    money_max_digits: int = Field(
        default=12, description="Maximum digits for money fields"
    )
    money_max_value: Decimal = Field(
        default=Decimal("10000000.00"), description="Maximum monetary value"
    )

    quantity_decimal_precision: int = Field(
        default=9, description="Decimal precision for quantities"
    )
    quantity_max_digits: int = Field(
        default=12, description="Maximum digits for quantity fields"
    )

    percentage_decimal_precision: int = Field(
        default=4, description="Decimal precision for percentages"
    )
    percentage_max_digits: int = Field(
        default=5, description="Maximum digits for percentage fields"
    )
    percentage_expected_sum: Decimal = Field(
        default=Decimal("1.0"), description="Expected sum of percentages"
    )
    percentage_tolerance: Decimal = Field(
        default=Decimal("0.0001"), description="Tolerance for validation"
    )


class StockSettings(BaseModel):
    """Shared settings for stock validation across modules.

    These settings are used in stock, broker, and event_bus modules.
    """

    model_config = ConfigDict(frozen=True)

    symbol_min_length: int = Field(
        default=4, ge=1, le=10, description="Minimum symbol length"
    )
    symbol_max_length: int = Field(
        default=4, ge=1, le=10, description="Maximum symbol length"
    )
    max_price: Decimal = Field(
        default=Decimal("1000000.00"), gt=0, description="Maximum stock price"
    )


class Settings(BaseModel):
    """Application configuration organized by module context."""

    model_config = ConfigDict(frozen=True)

    shared: SharedSettings = Field(default_factory=SharedSettings)
    stock: StockSettings = Field(default_factory=StockSettings)


settings = Settings()
