
from typing import Protocol
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from src.errors import BuyStockError, SellStockError, StockNotFoundError
import logging
import asyncio
import random
from src.fake_market import NASDAQ
from decimal import Decimal

class OperationType(Enum):
    BUY = "BUY"
    SELL = "SELL"

class BrokerOperation(BaseModel):
    date: datetime = datetime.now()
    symbol: str = Field(..., min_length=4, max_length=4, description="Symbol of the stock")
    
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

class Broker(Protocol):
    async def buy_stock_by_amount(self, request_data: BuyStockByAmountRequest) -> BuyStockResponse:
        ...
    async def buy_stock_by_quantity(self, request_data: BuyStockByQuantityRequest) -> BuyStockResponse:
        ...
    async def sell_stock_by_amount(self, request_data: SellStockByAmountRequest) -> SellStockResponse:
        ...
    async def sell_stock_by_quantity(self, request_data: SellStockByQuantityRequest) -> SellStockResponse:
        ...

class BanChileBroker:
    def __init__(self):
        logging.info("BanChileBroker, the best broker in the world, with the lower fees - initialized")
    
    async def buy_stock_by_amount(self, request_data: BuyStockByAmountRequest) -> BuyStockResponse:
        
        try:
            stock_current_info = NASDAQ.get(request_data.symbol)
            if not stock_current_info:
                raise StockNotFoundError(f"Stock {request_data.symbol} not found")
            
            logging.info(f"Buying {request_data.amount} of {request_data.symbol}")
            await asyncio.sleep(random.randint(1, 2))
            
            return BuyStockResponse(
                symbol=request_data.symbol,
                amount=request_data.amount,
                price=stock_current_info.price,
                quantity=request_data.amount / stock_current_info.price
            )
        except Exception as e:
            raise BuyStockError(str(e))
        
    async def buy_stock_by_quantity(self, request_data: BuyStockByQuantityRequest) -> BuyStockResponse:
        
        try:
            stock_current_info = NASDAQ.get(request_data.symbol)
            if not stock_current_info:
                raise StockNotFoundError(f"Stock {request_data.symbol} not found")
                
            logging.info(f"Buying {request_data.quantity} of {request_data.symbol}")
            await asyncio.sleep(random.randint(1, 2))
            
            return BuyStockResponse(
                symbol=request_data.symbol,
                amount=stock_current_info.price * request_data.quantity,
                price=stock_current_info.price,
                quantity=request_data.quantity
            )
        except Exception as e:
            raise BuyStockError(str(e))

    
    async def sell_stock_by_amount(self, request_data: SellStockByAmountRequest) -> SellStockResponse:
        
        try:
            stock_current_info = NASDAQ.get(request_data.symbol)
            if not stock_current_info:
                raise StockNotFoundError(f"Stock {request_data.symbol} not found")
            
            logging.info(f"Selling {request_data.amount} of {request_data.symbol}")
            await asyncio.sleep(random.randint(1, 2))
        
            return SellStockResponse(
                symbol=request_data.symbol,
                amount=request_data.amount,
                price=stock_current_info.price,
                quantity=request_data.amount / stock_current_info.price
            )
        except Exception as e:
            raise SellStockError(str(e))

    async def sell_stock_by_quantity(self, request_data: SellStockByQuantityRequest) -> SellStockResponse:
        
        try:
            stock_current_info = NASDAQ.get(request_data.symbol)
            if not stock_current_info:
                raise StockNotFoundError(f"Stock {request_data.symbol} not found")
            
            logging.info(f"Selling {request_data.quantity} of {request_data.symbol}")
            await asyncio.sleep(random.randint(1, 2))
        
            return SellStockResponse(
                symbol=request_data.symbol,
                amount=stock_current_info.price * request_data.quantity,
                price=stock_current_info.price,
                quantity=request_data.quantity
            )
        except Exception as e:
            raise SellStockError(str(e))