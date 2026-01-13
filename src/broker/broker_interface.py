from typing import Protocol
from src.broker.broker_dtos import (
    BuyStockByAmountRequest,
    BuyStockByQuantityRequest,
    SellStockByAmountRequest,
    SellStockByQuantityRequest,
    BuyStockResponse,
    SellStockResponse,
)


class Broker(Protocol):
    async def buy_stock_by_amount(
        self, request_data: BuyStockByAmountRequest
    ) -> BuyStockResponse: ...
    async def buy_stock_by_quantity(
        self, request_data: BuyStockByQuantityRequest
    ) -> BuyStockResponse: ...
    async def sell_stock_by_amount(
        self, request_data: SellStockByAmountRequest
    ) -> SellStockResponse: ...
    async def sell_stock_by_quantity(
        self, request_data: SellStockByQuantityRequest
    ) -> SellStockResponse: ...
