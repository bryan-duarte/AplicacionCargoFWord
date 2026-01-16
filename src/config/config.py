"""Application configuration settings organized by module context."""
from decimal import Decimal, getcontext
from pydantic import BaseModel, Field, ConfigDict

getcontext().prec = 28


class SharedSettings(BaseModel):
    """Shared settings between modules."""
    model_config = ConfigDict(frozen=True)

    money_decimal_precision: int = Field(default=2, description="Decimal precision for USD amounts")
    money_max_digits: int = Field(default=12, description="Maximum digits for money fields")
    money_min_value: Decimal = Field(default=Decimal("0.01"), description="Minimum monetary value")
    money_max_value: Decimal = Field(default=Decimal("10000000.00"), description="Maximum monetary value")

    quantity_decimal_precision: int = Field(default=9, description="Decimal precision for quantities")
    quantity_max_digits: int = Field(default=12, description="Maximum digits for quantity fields")
    quantity_min_buy: Decimal = Field(default=Decimal("0.01"), description="Minimum buy quantity")
    quantity_min_sell: Decimal = Field(default=Decimal("0.000001"), description="Minimum sell quantity")
    quantity_max: Decimal = Field(default=Decimal("1000000.000000000"), description="Maximum quantity")

    percentage_decimal_precision: int = Field(default=4, description="Decimal precision for percentages")
    percentage_max_digits: int = Field(default=5, description="Maximum digits for percentage fields")
    percentage_expected_sum: Decimal = Field(default=Decimal("1.0"), description="Expected sum of percentages")
    percentage_tolerance: Decimal = Field(default=Decimal("0.0001"), description="Tolerance for validation")


class StockSettings(BaseModel):
    """Specific settings for the Stock module."""
    model_config = ConfigDict(frozen=True)

    symbol_min_length: int = Field(default=4, ge=1, le=10, description="Minimum symbol length")
    symbol_max_length: int = Field(default=4, ge=1, le=10, description="Maximum symbol length")
    min_price: Decimal = Field(default=Decimal("0.01"), gt=0, description="Minimum stock price")
    max_price: Decimal = Field(default=Decimal("1000000.00"), gt=0, description="Maximum stock price")
    price_change_threshold_percent: Decimal = Field(
        default=Decimal("0.00"), ge=0, le=100, max_digits=5, decimal_places=2,
        description="Change threshold for price alerts"
    )


class BrokerSettings(BaseModel):
    """Specific settings for the Broker module."""
    model_config = ConfigDict(frozen=True)

    min_money: Decimal = Field(default=Decimal("0.01"), description="Minimum monetary value")
    max_money: Decimal = Field(default=Decimal("10000000.00"), description="Maximum monetary value")
    min_quantity_buy: Decimal = Field(default=Decimal("0.01"), description="Minimum buy quantity")
    min_quantity_sell: Decimal = Field(default=Decimal("0.000001"), description="Minimum sell quantity")
    max_quantity: Decimal = Field(default=Decimal("1000000.000000000"), description="Maximum quantity")
    min_delay_seconds: int = Field(default=1, ge=0, le=60, description="Minimum latency (seconds)")
    max_delay_seconds: int = Field(default=2, ge=0, le=60, description="Maximum latency (seconds)")
    batch_max_retries: int = Field(default=3, ge=1, le=10, description="Max retry attempts for rollback operations")
    batch_retry_delay_seconds: int = Field(default=1, ge=0, le=60, description="Delay between rollback retries (seconds)")
    batch_registry_max_size: int = Field(default=1000, ge=1, description="Maximum batches to track in registry")


class PortfolioSettings(BaseModel):
    """Specific settings for the Portfolio module."""
    model_config = ConfigDict(frozen=True)

    minimum_investment_usd: int = Field(
        default=1, gt=0, ge=1, le=1000000,
        description="Minimum allowed investment (USD)"
    )
    rebalance_threshold: Decimal = Field(
        default=Decimal("0.00"), max_digits=12, decimal_places=2,
        description="Difference threshold to trigger rebalancing"
    )
    retail_threshold_usd: int = Field(
        default=25000,
        description="Threshold for retail classification (USD)"
    )
    price_change_alert_threshold_percent: Decimal = Field(
        default=Decimal("0.00"), ge=0, le=100, max_digits=5, decimal_places=2,
        description="Price change threshold for alerts"
    )


class Settings(BaseModel):
    """Application configuration organized by module context."""
    model_config = ConfigDict(frozen=True)

    shared: SharedSettings = Field(default_factory=SharedSettings)
    stock: StockSettings = Field(default_factory=StockSettings)
    broker: BrokerSettings = Field(default_factory=BrokerSettings)
    portfolio: PortfolioSettings = Field(default_factory=PortfolioSettings)


settings = Settings()
