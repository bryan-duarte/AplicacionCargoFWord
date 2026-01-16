"""Broker operation DTOs."""
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, Union
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
from src.config.config import settings

# Default broker limits (can be overridden when creating DTOs)
_DEFAULT_MIN_MONEY = Decimal("0.01")
_DEFAULT_MAX_MONEY = Decimal("10000000.00")
_DEFAULT_MIN_QUANTITY_BUY = Decimal("0.01")
_DEFAULT_MIN_QUANTITY_SELL = Decimal("0.000001")
_DEFAULT_MAX_QUANTITY = Decimal("1000000.000000000")


class OperationType(Enum):
    BUY = "BUY"
    SELL = "SELL"

class OperationStatus(Enum):
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"

class OperationState(Enum):
    """States for batch operation tracking."""
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"
    ROLLED_BACK = "ROLLED_BACK"

class BatchOperationEntry(BaseModel):
    """Entry in broker's internal batch registry."""
    operation_uuid: UUID
    operation_schema: Union[
        "BuyStockByAmountRequest",
        "BuyStockByQuantityRequest",
        "SellStockByAmountRequest",
        "SellStockByQuantityRequest",
    ]
    state: OperationState
    response: Optional[Union["BuyStockResponse", "SellStockResponse"]] = None
    rollback_attempt: int = 0

class BrokerOperation(BaseModel):
    date: datetime = datetime.now()
    symbol: str = Field(
        ...,
        min_length=settings.stock.symbol_min_length,
        max_length=settings.stock.symbol_max_length,
        description="Symbol of the stock",
    )
    batch_uuid: Optional[UUID] = Field(
        default=None,
        description="Batch UUID for grouping atomic operations",
    )
    rollback: bool = Field(
        default=False,
        description="Whether this is a rollback operation",
    )


class BuyStockByAmountRequest(BrokerOperation):
    uuid: UUID = Field(
        default_factory=uuid4, description="Unique identifier for the operation"
    )
    operation_type: OperationType = OperationType.BUY
    amount: Decimal = Field(
        ...,
        gt=0,
        ge=_DEFAULT_MIN_MONEY,
        le=_DEFAULT_MAX_MONEY,
        max_digits=settings.shared.money_max_digits,
        decimal_places=settings.shared.money_decimal_precision,
        description="Amount of money to buy (USD, max $10M)",
    )

    def __repr__(self) -> str:
        return f"BuyStockRequest(symbol={self.symbol}, amount={self.amount})"


class BuyStockByQuantityRequest(BrokerOperation):
    uuid: UUID = Field(
        default_factory=uuid4, description="Unique identifier for the operation"
    )
    operation_type: OperationType = OperationType.BUY
    quantity: Decimal = Field(
        ...,
        gt=0,
        ge=_DEFAULT_MIN_QUANTITY_BUY,
        le=_DEFAULT_MAX_QUANTITY,
        max_digits=settings.shared.quantity_max_digits,
        decimal_places=settings.shared.quantity_decimal_precision,
        description="Quantity of the stock to buy (supports fractional shares)",
    )

    def __repr__(self) -> str:
        return f"BuyStockRequest(symbol={self.symbol}, quantity={self.quantity})"


class BuyStockResponse(BrokerOperation):
    uuid: UUID
    operation_type: OperationType = OperationType.BUY
    status: OperationStatus = OperationStatus.SUCCESS
    status_message: str = Field(
        default="Buy operation executed successfully.",
        description="Human readable summary of the broker outcome",
    )
    amount: Decimal = Field(
        ...,
        gt=0,
        max_digits=settings.shared.money_max_digits,
        decimal_places=settings.shared.money_decimal_precision,
        description="Amount of money spent USD",
    )
    price: Decimal = Field(
        ...,
        gt=0,
        max_digits=settings.shared.money_max_digits,
        decimal_places=settings.shared.money_decimal_precision,
        description="Price per share USD",
    )
    quantity: Decimal = Field(
        ...,
        gt=0,
        max_digits=settings.shared.quantity_max_digits,
        decimal_places=settings.shared.quantity_decimal_precision,
        description="Quantity of shares purchased",
    )

    def to_rollback_request(self) -> "SellStockByQuantityRequest":
        """Generate a sell request to rollback this buy operation."""
        return SellStockByQuantityRequest(
            symbol=self.symbol,
            quantity=self.quantity,
            batch_uuid=self.batch_uuid,
            rollback=True,
        )

    def __repr__(self) -> str:
        return f"BuyStockResponse(symbol={self.symbol}, amount={self.amount}, price={self.price}, quantity={self.quantity})"


class SellStockByAmountRequest(BrokerOperation):
    uuid: UUID = Field(
        default_factory=uuid4, description="Unique identifier for the operation"
    )
    operation_type: OperationType = OperationType.SELL
    amount: Decimal = Field(
        ...,
        gt=0,
        ge=_DEFAULT_MIN_MONEY,
        le=_DEFAULT_MAX_MONEY,
        max_digits=settings.shared.money_max_digits,
        decimal_places=settings.shared.money_decimal_precision,
        description="Amount of money to sell USD",
    )

    def __repr__(self) -> str:
        return f"SellStockRequest(symbol={self.symbol}, amount={self.amount})"

class SellStockByQuantityRequest(BrokerOperation):
    uuid: UUID = Field(
        default_factory=uuid4, description="Unique identifier for the operation"
    )
    operation_type: OperationType = OperationType.SELL
    quantity: Decimal = Field(
        ...,
        gt=0,
        ge=_DEFAULT_MIN_QUANTITY_SELL,
        le=_DEFAULT_MAX_QUANTITY,
        max_digits=settings.shared.quantity_max_digits,
        decimal_places=settings.shared.quantity_decimal_precision,
        description="Quantity of the stock to sell (supports fractional shares)",
    )

    def __repr__(self) -> str:
        return f"SellStockRequest(symbol={self.symbol}, quantity={self.quantity})"

class SellStockResponse(BrokerOperation):
    uuid: UUID
    operation_type: OperationType = OperationType.SELL
    status: OperationStatus = OperationStatus.SUCCESS
    status_message: str = Field(
        default="Sell operation executed successfully.",
        description="Human readable summary of the broker outcome",
    )
    amount: Decimal = Field(
        ...,
        gt=0,
        max_digits=settings.shared.money_max_digits,
        decimal_places=settings.shared.money_decimal_precision,
        description="Amount of money received (USD)",
    )
    price: Decimal = Field(
        ...,
        gt=0,
        max_digits=settings.shared.money_max_digits,
        decimal_places=settings.shared.money_decimal_precision,
        description="Price per share (USD)",
    )
    quantity: Decimal = Field(
        ...,
        gt=0,
        max_digits=settings.shared.quantity_max_digits,
        decimal_places=settings.shared.quantity_decimal_precision,
        description="Quantity of shares sold",
    )

    def to_rollback_request(self) -> "BuyStockByQuantityRequest":
        """Generate a buy request to rollback this sell operation."""
        return BuyStockByQuantityRequest(
            symbol=self.symbol,
            quantity=self.quantity,
            batch_uuid=self.batch_uuid,
            rollback=True,
        )

    def __repr__(self) -> str:
        return f"SellStockResponse(symbol={self.symbol}, amount={self.amount}, price={self.price}, quantity={self.quantity})"
