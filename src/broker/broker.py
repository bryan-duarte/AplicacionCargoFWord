from src.broker.broker_dtos import (
    BuyStockByAmountRequest,
    BuyStockByQuantityRequest,
    SellStockByAmountRequest,
    SellStockByQuantityRequest,
    BuyStockResponse,
    SellStockResponse,
)
from src.errors.errors import (
    StockNotFoundError,
    BuyStockError,
    SellStockError,
    BrokerConnectionError,
)
from src.fake_market.fake_market import NASDAQ
from src.utils.decimal_utils import quantize_quantity, quantize_money
import logging
import asyncio
import random


class BanChileBroker:
    def __init__(self):
        logging.info(
            "BanChileBroker, the best broker in the world, with the lower fees - initialized"
        )

    async def buy_stock_by_amount(
        self, request_data: BuyStockByAmountRequest
    ) -> BuyStockResponse:
        operation_uuid = request_data.uuid
        try:
            stock_current_info = NASDAQ.get(request_data.symbol)
            if not stock_current_info:
                raise StockNotFoundError(
                    f"Stock {request_data.symbol} not found",
                    operation_uuid=operation_uuid,
                )

            await asyncio.sleep(random.randint(1, 2))

            return BuyStockResponse(
                uuid=operation_uuid,
                symbol=request_data.symbol,
                amount=request_data.amount,
                price=stock_current_info.price,
                quantity=quantize_quantity(request_data.amount / stock_current_info.price),
            )
        except BrokerConnectionError as e:
            raise BrokerConnectionError(
                str(e), operation_uuid=operation_uuid
            ) from e
        except Exception as e:
            raise BuyStockError(str(e), operation_uuid=operation_uuid) from e

    async def buy_stock_by_quantity(
        self, request_data: BuyStockByQuantityRequest
    ) -> BuyStockResponse:
        operation_uuid = request_data.uuid
        try:
            stock_current_info = NASDAQ.get(request_data.symbol)
            if not stock_current_info:
                raise StockNotFoundError(
                    f"Stock {request_data.symbol} not found",
                    operation_uuid=operation_uuid,
                )

            await asyncio.sleep(random.randint(1, 2))

            return BuyStockResponse(
                uuid=operation_uuid,
                symbol=request_data.symbol,
                amount=quantize_money(stock_current_info.price * request_data.quantity),
                price=stock_current_info.price,
                quantity=request_data.quantity,
            )
        except BrokerConnectionError as e:
            raise BrokerConnectionError(
                str(e), operation_uuid=operation_uuid
            ) from e
        except Exception as e:
            raise BuyStockError(str(e), operation_uuid=operation_uuid) from e

    async def sell_stock_by_amount(
        self, request_data: SellStockByAmountRequest
    ) -> SellStockResponse:
        operation_uuid = request_data.uuid
        try:
            stock_current_info = NASDAQ.get(request_data.symbol)
            if not stock_current_info:
                raise StockNotFoundError(
                    f"Stock {request_data.symbol} not found",
                    operation_uuid=operation_uuid,
                )

            await asyncio.sleep(random.randint(1, 2))

            return SellStockResponse(
                uuid=operation_uuid,
                symbol=request_data.symbol,
                amount=request_data.amount,
                price=stock_current_info.price,
                quantity=quantize_quantity(request_data.amount / stock_current_info.price),
            )
        except BrokerConnectionError as e:
            raise BrokerConnectionError(
                str(e), operation_uuid=operation_uuid
            ) from e
        except Exception as e:
            raise SellStockError(str(e), operation_uuid=operation_uuid) from e

    async def sell_stock_by_quantity(
        self, request_data: SellStockByQuantityRequest
    ) -> SellStockResponse:
        operation_uuid = request_data.uuid
        try:
            stock_current_info = NASDAQ.get(request_data.symbol)
            if not stock_current_info:
                raise StockNotFoundError(
                    f"Stock {request_data.symbol} not found",
                    operation_uuid=operation_uuid,
                )

            await asyncio.sleep(random.randint(1, 2))

            return SellStockResponse(
                uuid=operation_uuid,
                symbol=request_data.symbol,
                amount=quantize_money(stock_current_info.price * request_data.quantity),
                price=stock_current_info.price,
                quantity=request_data.quantity,
            )
        except BrokerConnectionError as e:
            raise BrokerConnectionError(
                str(e), operation_uuid=operation_uuid
            ) from e
        except Exception as e:
            raise SellStockError(str(e), operation_uuid=operation_uuid) from e
