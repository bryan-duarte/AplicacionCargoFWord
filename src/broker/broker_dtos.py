from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from decimal import Decimal


class OperationType(Enum):
    BUY = "BUY"
    SELL = "SELL"


class BrokerOperation(BaseModel):
    date: datetime = datetime.now()
    symbol: str = Field(
        ..., min_length=4, max_length=4, description="Symbol of the stock"
    )


class BuyStockByAmountRequest(BrokerOperation):
    operation_type: OperationType = OperationType.BUY
    amount: Decimal = Field(..., gt=0, description="Amount of money to buy")

    def __repr__(self) -> str:
        return f"BuyStockRequest(symbol={self.symbol}, amount={self.amount})"


class BuyStockByQuantityRequest(BrokerOperation):
    operation_type: OperationType = OperationType.BUY
    quantity: Decimal = Field(..., gt=0, description="Quantity of the stock to buy")

    def __repr__(self) -> str:
        return f"BuyStockRequest(symbol={self.symbol}, quantity={self.quantity})"


class BuyStockResponse(BrokerOperation):
    operation_type: OperationType = OperationType.BUY
    amount: Decimal = Field(..., gt=0, description="Amount of money to buy")
    price: Decimal = Field(..., gt=0, description="Price of the stock")
    quantity: Decimal = Field(..., gt=0, description="Quantity of the stock")

    def __repr__(self) -> str:
        return f"BuyStockResponse(symbol={self.symbol}, amount={self.amount}, price={self.price}, quantity={self.quantity})"


class SellStockByAmountRequest(BrokerOperation):
    operation_type: OperationType = OperationType.SELL
    amount: Decimal = Field(..., gt=0, description="Amount of money to sell")

    def __repr__(self) -> str:
        return f"SellStockRequest(symbol={self.symbol}, amount={self.amount})"


class SellStockByQuantityRequest(BrokerOperation):
    operation_type: OperationType = OperationType.SELL
    quantity: Decimal = Field(..., gt=0, description="Quantity of the stock to sell")

    def __repr__(self) -> str:
        return f"SellStockRequest(symbol={self.symbol}, quantity={self.quantity})"


class SellStockResponse(BrokerOperation):
    operation_type: OperationType = OperationType.SELL
    amount: Decimal = Field(..., gt=0, description="Amount of money to sell")
    price: Decimal = Field(..., gt=0, description="Price of the stock")
    quantity: Decimal = Field(..., gt=0, description="Quantity of the stock")

    def __repr__(self) -> str:
        return f"SellStockResponse(symbol={self.symbol}, amount={self.amount}, price={self.price}, quantity={self.quantity})"
