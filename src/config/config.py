"""Application configuration settings."""
from decimal import Decimal, getcontext
from pydantic import BaseModel, Field, ConfigDict

getcontext().prec = 28


class DecimalPrecision(BaseModel):
    """Decimal precision settings for quantization operations."""
    model_config = ConfigDict(frozen=True)

    max: int = Field(
        default=9,
        description="Maximum precision for fractional shares (0.000000001)"
    )
    money: int = Field(
        default=2,
        description="Precision for USD amounts and prices (cents)"
    )
    quantity: int = Field(
        default=9,
        description="Precision for fractional share quantities"
    )
    percentage: int = Field(
        default=4,
        description="Precision for allocation percentages"
    )


class BrokerLimits(BaseModel):
    """Broker operation limits and thresholds."""
    model_config = ConfigDict(frozen=True)

    min_money: Decimal = Field(
        default=Decimal("0.01"),
        description="Minimum monetary value (1 cent)"
    )
    max_money: Decimal = Field(
        default=Decimal("10000000.00"),
        description="Maximum monetary value ($10M)"
    )
    min_quantity_buy: Decimal = Field(
        default=Decimal("0.01"),
        description="Minimum quantity for buy operations"
    )
    min_quantity_sell: Decimal = Field(
        default=Decimal("0.000001"),
        description="Minimum quantity for sell operations"
    )
    max_quantity: Decimal = Field(
        default=Decimal("1000000.000000000"),
        description="Maximum quantity for operations"
    )


class ValidationThresholds(BaseModel):
    """Thresholds for validation operations."""
    model_config = ConfigDict(frozen=True)

    percentage_tolerance: Decimal = Field(
        default=Decimal("0.0001"),
        description="Tolerance for percentage validation (0.01%)"
    )
    percentage_sum: Decimal = Field(
        default=Decimal("1.0"),
        description="Expected sum of percentages (100%)"
    )


class PydanticConstraints(BaseModel):
    """Max digits constraints for Pydantic Field validation."""
    model_config = ConfigDict(frozen=True)

    money: int = Field(
        default=12,
        description="Max digits for money fields (supports up to 9,999,999,999.99)"
    )
    quantity: int = Field(
        default=12,
        description="Max digits for quantity fields"
    )
    percentage: int = Field(
        default=5,
        description="Max digits for percentage fields"
    )


class Settings(BaseModel):
    """Application settings."""
    model_config = ConfigDict(frozen=True)

    decimal_precision: DecimalPrecision = Field(
        default_factory=DecimalPrecision
    )
    broker_limits: BrokerLimits = Field(
        default_factory=BrokerLimits
    )
    validation_thresholds: ValidationThresholds = Field(
        default_factory=ValidationThresholds
    )
    pydantic_constraints: PydanticConstraints = Field(
        default_factory=PydanticConstraints
    )

    minimum_investment: int = Field(
        default=1,
        gt=0,
        ge=1,
        le=1000000,
        description="Minimum investment amount required (USD)"
    )
    retail_threshold: int = Field(
        default=25000,
        description="Threshold for retail portfolio classification (USD)"
    )
    balance_threshold: Decimal = Field(
        default=Decimal("0.00"),
        max_digits=12,
        decimal_places=2,
        description="Minimum balance threshold for rebalancing operations (USD)"
    )
    stock_price_change_threshold: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
        le=100,
        max_digits=5,
        decimal_places=2,
        description="Percentage threshold for stock price change alerts (0-100%)"
    )


settings = Settings()
