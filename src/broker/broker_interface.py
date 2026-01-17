from abc import ABC, abstractmethod
from uuid import UUID

from src.broker.broker_dtos import (
    BuyStockByAmountRequest,
    BuyStockByQuantityRequest,
    BuyStockResponse,
    SellStockByAmountRequest,
    SellStockByQuantityRequest,
    SellStockResponse,
)


class Broker(ABC):
    """Abstract broker contract enforcing all trade operations."""

    @abstractmethod
    async def buy_stock_by_amount(
        self, request_data: BuyStockByAmountRequest
    ) -> BuyStockResponse:
        raise NotImplementedError(
            f"buy_stock_by_amount must be implemented in broker implementation. {self.__class__.__name__}"
        )

    @abstractmethod
    async def buy_stock_by_quantity(
        self, request_data: BuyStockByQuantityRequest
    ) -> BuyStockResponse:
        raise NotImplementedError(
            f"buy_stock_by_quantity must be implemented in broker implementation. {self.__class__.__name__}"
        )

    @abstractmethod
    async def sell_stock_by_amount(
        self, request_data: SellStockByAmountRequest
    ) -> SellStockResponse:
        raise NotImplementedError(
            f"sell_stock_by_amount must be implemented in broker implementation. {self.__class__.__name__}"
        )

    @abstractmethod
    async def sell_stock_by_quantity(
        self, request_data: SellStockByQuantityRequest
    ) -> SellStockResponse:
        raise NotImplementedError(
            f"sell_stock_by_quantity must be implemented in broker implementation. {self.__class__.__name__}"
        )

    @abstractmethod
    async def batch_rollback(self, batch_uuid: UUID) -> bool:
        raise NotImplementedError(
            f"batch_rollback must be implemented in broker implementation. {self.__class__.__name__}"
        )
