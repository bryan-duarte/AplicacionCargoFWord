"""Broker operation DTOs."""
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from decimal import Decimal
from uuid import UUID, uuid4
from src.config.config import settings


class OperationType(Enum):
    BUY = "BUY"
    SELL = "SELL"


class OperationStatus(Enum):
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"


class BrokerOperation(BaseModel):
    date: datetime = datetime.now()
    symbol: str = Field(
        ...,
        min_length=settings.stock.symbol_min_length,
        max_length=settings.stock.symbol_max_length,
        description="Symbol of the stock"
    )


class BuyStockByAmountRequest(BrokerOperation):
    uuid: UUID = Field(
        default_factory=uuid4, description="Unique identifier for the operation"
    )
    operation_type: OperationType = OperationType.BUY
    amount: Decimal = Field(
        ...,
        gt=0,
        ge=settings.broker.min_money,
        le=settings.broker.max_money,
        max_digits=settings.shared.money_max_digits,
        decimal_places=settings.shared.money_decimal_precision,
        description="Amount of money to buy (USD, max $10M)"
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
        ge=settings.broker.min_quantity_buy,
        le=settings.broker.max_quantity,
        max_digits=settings.shared.quantity_max_digits,
        decimal_places=settings.shared.quantity_decimal_precision,
        description="Quantity of the stock to buy (supports fractional shares)"
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
        description="Amount of money spent USD"
    )
    price: Decimal = Field(
        ...,
        gt=0,
        max_digits=settings.shared.money_max_digits,
        decimal_places=settings.shared.money_decimal_precision,
        description="Price per share USD"
    )
    quantity: Decimal = Field(
        ...,
        gt=0,
        max_digits=settings.shared.quantity_max_digits,
        decimal_places=settings.shared.quantity_decimal_precision,
        description="Quantity of shares purchased"
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
        ge=settings.broker.min_money,
        le=settings.broker.max_money,
        max_digits=settings.shared.money_max_digits,
        decimal_places=settings.shared.money_decimal_precision,
        description="Amount of money to sell USD"
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
        ge=settings.broker.min_quantity_sell,
        le=settings.broker.max_quantity,
        max_digits=settings.shared.quantity_max_digits,
        decimal_places=settings.shared.quantity_decimal_precision,
        description="Quantity of the stock to sell (supports fractional shares)"
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
        description="Amount of money received (USD)"
    )
    price: Decimal = Field(
        ...,
        gt=0,
        max_digits=settings.shared.money_max_digits,
        decimal_places=settings.shared.money_decimal_precision,
        description="Price per share (USD)"
    )
    quantity: Decimal = Field(
        ...,
        gt=0,
        max_digits=settings.shared.quantity_max_digits,
        decimal_places=settings.shared.quantity_decimal_precision,
        description="Quantity of shares sold"
    )

    def __repr__(self) -> str:
        return f"SellStockResponse(symbol={self.symbol}, amount={self.amount}, price={self.price}, quantity={self.quantity})"
