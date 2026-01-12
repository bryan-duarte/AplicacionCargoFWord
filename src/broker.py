
from typing import Protocol
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from src.errors import BuyStockError, SellStockError
import logging
import asyncio
import random

FAKE_MARKET = {
    "AAPL": 250,
    "META": 600,
    "MSFT": 200,
    "TSLA": 100,
    "AMZN": 150,
}

class OperationType(Enum):
    BUY = "BUY"
    SELL = "SELL"

class BrokerOperation(BaseModel):
    date: datetime = datetime.now()
    symbol: str = Field(..., min_length=4, max_length=4, description="Symbol of the stock")
    
class BuyStockRequest(BrokerOperation):
    operation_type: OperationType = OperationType.BUY
    amount: float = Field(..., gt=0, description="Amount of money to buy")
    
    def __repr__(self) -> str:
        return f"BuyStockRequest(symbol={self.symbol}, amount={self.amount})"

class BuyStockResponse(BrokerOperation):
    operation_type: OperationType = OperationType.BUY
    amount: float = Field(..., gt=0, description="Amount of money to buy")
    price: float = Field(..., gt=0, description="Price of the stock")
    quantity: float = Field(..., gt=0, description="Quantity of the stock")
    
    def __repr__(self) -> str:
        return f"BuyStockResponse(symbol={self.symbol}, amount={self.amount}, price={self.price}, quantity={self.quantity})"
    
class SellStockRequest(BrokerOperation):
    operation_type: OperationType = OperationType.SELL
    amount: float = Field(..., gt=0, description="Amount of money to sell")
    
    def __repr__(self) -> str:
        return f"SellStockRequest(symbol={self.symbol}, amount={self.amount})"

class SellStockResponse(BrokerOperation):
    operation_type: OperationType = OperationType.SELL
    amount: float = Field(..., gt=0, description="Amount of money to sell")
    price: float = Field(..., gt=0, description="Price of the stock")
    quantity: float = Field(..., gt=0, description="Quantity of the stock")    
    
    def __repr__(self) -> str:
        return f"SellStockResponse(symbol={self.symbol}, amount={self.amount}, price={self.price}, quantity={self.quantity})"

class Broker(Protocol):
    async def buy_stock_by_amount(self, request_data: BuyStockRequest) -> BuyStockResponse:
        ...
    async def sell_stock_by_amount(self, request_data: SellStockRequest) -> SellStockResponse:
        ...

class BanChileBroker:
    def __init__(self):
        logging.info("BanChileBroker, the best broker in the world, with the lower fees - initialized")
    
    async def buy_stock_by_amount(self, request_data: BuyStockRequest) -> BuyStockResponse:
        
        try:
            price = FAKE_MARKET[request_data.symbol]
            
            logging.info(f"Buying {request_data.amount} of {request_data.symbol}")
            await asyncio.sleep(random.randint(1, 2))
            
            return BuyStockResponse(
                symbol=request_data.symbol,
                amount=request_data.amount,
                price=price,
                quantity=request_data.amount / price
            )
        except Exception as e:
            raise BuyStockError(str(e))
    
    async def sell_stock_by_amount(self, request_data: SellStockRequest) -> SellStockResponse:
        
        try:
            price = FAKE_MARKET[request_data.symbol]
            
            logging.info(f"Selling {request_data.amount} of {request_data.symbol}")
            await asyncio.sleep(random.randint(1, 2))
        
            return SellStockResponse(
                symbol=request_data.symbol,
                amount=request_data.amount,
                price=price,
                quantity=request_data.amount / price
            )
        except Exception as e:
            raise SellStockError(str(e))