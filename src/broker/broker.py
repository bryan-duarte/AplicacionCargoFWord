from src.broker.broker_dtos import (
    BuyStockByAmountRequest,
    BuyStockByQuantityRequest,
    SellStockByAmountRequest,
    SellStockByQuantityRequest,
    BuyStockResponse,
    SellStockResponse,
)
from src.errors.errors import StockNotFoundError, BuyStockError, SellStockError
from src.fake_market.fake_market import NASDAQ
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
                quantity=request_data.amount / stock_current_info.price,
            )
        except Exception as e:
            raise BuyStockError(str(e))

    async def buy_stock_by_quantity(
        self, request_data: BuyStockByQuantityRequest
    ) -> BuyStockResponse:
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
                quantity=request_data.quantity,
            )
        except Exception as e:
            raise BuyStockError(str(e))

    async def sell_stock_by_amount(
        self, request_data: SellStockByAmountRequest
    ) -> SellStockResponse:
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
                quantity=request_data.amount / stock_current_info.price,
            )
        except Exception as e:
            raise SellStockError(str(e))

    async def sell_stock_by_quantity(
        self, request_data: SellStockByQuantityRequest
    ) -> SellStockResponse:
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
                quantity=request_data.quantity,
            )
        except Exception as e:
            raise SellStockError(str(e))
