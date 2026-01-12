from src.stock import Stock
from pydantic import BaseModel, ConfigDict, Field
from src.broker import Broker, BuyStockRequest, BuyStockResponse
from asyncio import Future
import asyncio
from typing import Awaitable
from src.config import settings
from src.portfolio_register import portfolio_registry

class PortfolioValue(BaseModel):
    total_value: float = Field(..., gt=0, description="Total value of the portfolio")
    is_retail: bool = Field(..., description="Is the portfolio a retail portfolio?")

class StockToAllocate(BaseModel):
    stock: Stock
    percentage: float = Field(..., gt=0, le=1, description="Percentage of the stock to allocate")
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        frozen=True,
    )
    
class AllocatedStock(BaseModel):
    stock: Stock
    percentage: float = Field(..., gt=0, le=1, description="Percentage of the stock to allocate")
    quantity: float = Field(..., gt=0, description="Quantity of the stock")
    total_value: float = Field(..., gt=0, description="Total value of the stock")
    price: float = Field(..., gt=0, description="Price of the stock")
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        frozen=True,
    )
    
    def __repr__(self) -> str:
        return f"AllocatedStock - Percentage: {self.percentage * 100}% - Quantity: {self.quantity} - Total Value: {self.total_value}"


class Portfolio:
    def __init__(self, initial_investment: int, stocks_to_allocate: list[StockToAllocate], broker: Broker, portfolio_name: str):
        self._portfolio_name = portfolio_name
        if initial_investment < settings.minimum_investment:
            raise ValueError(f"Initial investment must be greater than or equal to {settings.minimum_investment}")
        
        self._initial_investment = initial_investment
        self._stock_to_allocate : dict[str, StockToAllocate] = {}
        self._allocated_stocks : dict[str, AllocatedStock] = {}
        self._broker = broker
        
        self._set_stock_to_allocate(stocks_to_allocate)
        portfolio_registry.add(self)
    
    @property
    def portfolio_name(self) -> str:
        return self._portfolio_name
    
    @property
    def allocated_stocks(self) -> dict[str, AllocatedStock]:
        return self._allocated_stocks
    
    def get_total_value(self) -> PortfolioValue:
        total_value = sum(stock.total_value for stock in self._allocated_stocks.values())
        is_retail = total_value < settings.retail_threshold
        
        return PortfolioValue(total_value=total_value, is_retail=is_retail)

    def _set_stock_to_allocate(self, stocks_to_allocate: list[StockToAllocate]) -> None:
        for stock in stocks_to_allocate:
            self._stock_to_allocate[stock.stock.symbol] = stock
    
    async def initialize(self) -> None:

        broker = self._broker
        
        buy_operations : list[Awaitable[BuyStockResponse]] = [
            broker.buy_stock_by_amount(
                BuyStockRequest(
                    symbol=stock.stock.symbol,
                    amount=self._initial_investment * stock.percentage
                )
            ) 
            for stock in self._stock_to_allocate.values()
        ]
        
        
        bougth_stocks_list : list[BuyStockResponse] = await asyncio.gather(*buy_operations)
        
        for bougth_stock in bougth_stocks_list:
            
            self._allocated_stocks[bougth_stock.symbol] = AllocatedStock(
                stock=Stock(symbol=bougth_stock.symbol, price=bougth_stock.price),
                percentage=self._stock_to_allocate[bougth_stock.symbol].percentage,
                quantity=bougth_stock.quantity,
                total_value=bougth_stock.amount,
                price=bougth_stock.price
            )
    
    def __repr__(self) -> str:
        return f"""
            Portfolio(
                portfolio_name={self._portfolio_name},
                initial_investment={self._initial_investment}, 
                allocated_stocks={self._allocated_stocks}
            )
        """