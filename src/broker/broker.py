from src.broker.broker_dtos import (
    BuyStockByAmountRequest,
    BuyStockByQuantityRequest,
    SellStockByAmountRequest,
    SellStockByQuantityRequest,
    BuyStockResponse,
    SellStockResponse,
    BatchOperationEntry,
    OperationState,
)
from src.broker.broker_interface import Broker
from src.broker.errors import (
    StockNotFoundError,
    BuyStockError,
    SellStockError,
    BrokerConnectionError,
)
from src.utils.fake_market import NASDAQ
from src.utils.decimal_utils import quantize_quantity, quantize_money
from src.config.config import settings
from datetime import datetime
from typing import Optional, Union
from uuid import UUID
import asyncio
import logging
import random


class BanChileBroker(Broker):
    def __init__(self):
        logging.info(
            "BanChileBroker, the best broker in the world, with the lower fees - initialized"
        )
        self._batch_registry: dict[UUID, dict[UUID, BatchOperationEntry]] = {}

    def _register_operation(
        self,
        operation: Union[
            BuyStockByAmountRequest,
            BuyStockByQuantityRequest,
            SellStockByAmountRequest,
            SellStockByQuantityRequest,
        ],
    ) -> None:
        """Register an operation in the batch registry."""
        if operation.batch_uuid is None:
            return

        if operation.batch_uuid not in self._batch_registry:
            self._batch_registry[operation.batch_uuid] = {}

        self._batch_registry[operation.batch_uuid][operation.uuid] = BatchOperationEntry(
            operation_uuid=operation.uuid,
            operation_schema=operation,
            state=OperationState.PENDING,
        )

    def _mark_operation_success(
        self,
        operation_uuid: UUID,
        batch_uuid: Optional[UUID],
        response: Union[BuyStockResponse, SellStockResponse],
    ) -> None:
        """Mark an operation as successful."""
        
        not_batch_operation = batch_uuid is None or batch_uuid not in self._batch_registry
        if not_batch_operation:
            return
        if operation_uuid in self._batch_registry[batch_uuid]:
            batch_registry_entry = self._batch_registry[batch_uuid][operation_uuid]
            batch_registry_entry.state = OperationState.SUCCESS
            batch_registry_entry.response = response

    def _mark_operation_error(
        self,
        operation_uuid: UUID,
        batch_uuid: Optional[UUID],
    ) -> None:
        """Mark an operation as failed."""
        not_batch_operation = batch_uuid is None or batch_uuid not in self._batch_registry
        if not_batch_operation:
            return
        if operation_uuid in self._batch_registry[batch_uuid]:
            self._batch_registry[batch_uuid][operation_uuid].state = OperationState.ERROR

    async def buy_stock_by_amount(
        self, request_data: BuyStockByAmountRequest
    ) -> BuyStockResponse:
        operation_uuid = request_data.uuid
        batch_uuid = request_data.batch_uuid

        self._register_operation(request_data)

        try:
            stock_current_info = NASDAQ.get(request_data.symbol)
            if not stock_current_info:
                self._mark_operation_error(operation_uuid, batch_uuid)
                raise StockNotFoundError(
                    f"Stock {request_data.symbol} not found",
                    operation_uuid=operation_uuid,
                )

            await asyncio.sleep(
                random.randint(settings.broker.min_delay_seconds, settings.broker.max_delay_seconds)
            )

            response = BuyStockResponse(
                uuid=operation_uuid,
                symbol=request_data.symbol,
                amount=request_data.amount,
                price=stock_current_info.price,
                quantity=quantize_quantity(request_data.amount / stock_current_info.price),
                batch_uuid=batch_uuid,
                rollback=request_data.rollback,
            )

            self._mark_operation_success(operation_uuid, batch_uuid, response)
            return response
        except BrokerConnectionError as e:
            self._mark_operation_error(operation_uuid, batch_uuid)
            raise BrokerConnectionError(str(e), operation_uuid=operation_uuid) from e
        except Exception as e:
            self._mark_operation_error(operation_uuid, batch_uuid)
            raise BuyStockError(str(e), operation_uuid=operation_uuid) from e

    async def buy_stock_by_quantity(
        self, request_data: BuyStockByQuantityRequest
    ) -> BuyStockResponse:
        OPERATION_UUID = request_data.uuid
        BATCH_UUID = request_data.batch_uuid

        self._register_operation(request_data)

        try:
            stock_current_info = NASDAQ.get(request_data.symbol)
            if not stock_current_info:
                self._mark_operation_error(OPERATION_UUID, BATCH_UUID)
                raise StockNotFoundError(
                    f"Stock {request_data.symbol} not found",
                    operation_uuid=OPERATION_UUID,
                )

            await asyncio.sleep(
                random.randint(settings.broker.min_delay_seconds, settings.broker.max_delay_seconds)
            )

            response = BuyStockResponse(
                uuid=OPERATION_UUID,
                symbol=request_data.symbol,
                amount=quantize_money(stock_current_info.price * request_data.quantity),
                price=stock_current_info.price,
                quantity=request_data.quantity,
                batch_uuid=BATCH_UUID,
                rollback=request_data.rollback,
            )

            self._mark_operation_success(OPERATION_UUID, BATCH_UUID, response)
            return response
        except BrokerConnectionError as e:
            self._mark_operation_error(OPERATION_UUID, BATCH_UUID)
            raise BrokerConnectionError(str(e), operation_uuid=OPERATION_UUID) from e
        except Exception as e:
            self._mark_operation_error(OPERATION_UUID, BATCH_UUID)
            raise BuyStockError(str(e), operation_uuid=OPERATION_UUID) from e

    async def sell_stock_by_amount(
        self, request_data: SellStockByAmountRequest
    ) -> SellStockResponse:
        OPERATION_UUID = request_data.uuid
        BATCH_UUID = request_data.batch_uuid

        self._register_operation(request_data)

        try:
            stock_current_info = NASDAQ.get(request_data.symbol)
            if not stock_current_info:
                self._mark_operation_error(OPERATION_UUID, BATCH_UUID)
                raise StockNotFoundError(
                    f"Stock {request_data.symbol} not found",
                    operation_uuid=OPERATION_UUID,
                )

            await asyncio.sleep(
                random.randint(settings.broker.min_delay_seconds, settings.broker.max_delay_seconds)
            )

            response = SellStockResponse(
                uuid=OPERATION_UUID,
                symbol=request_data.symbol,
                amount=request_data.amount,
                price=stock_current_info.price,
                quantity=quantize_quantity(request_data.amount / stock_current_info.price),
                batch_uuid=BATCH_UUID,
                rollback=request_data.rollback,
            )

            self._mark_operation_success(OPERATION_UUID, BATCH_UUID, response)
            return response
        except BrokerConnectionError as e:
            self._mark_operation_error(OPERATION_UUID, BATCH_UUID)
            raise BrokerConnectionError(str(e), operation_uuid=OPERATION_UUID) from e
        except Exception as e:
            self._mark_operation_error(OPERATION_UUID, BATCH_UUID)
            raise SellStockError(str(e), operation_uuid=OPERATION_UUID) from e

    async def sell_stock_by_quantity(
        self, request_data: SellStockByQuantityRequest
    ) -> SellStockResponse:
        OPERATION_UUID = request_data.uuid
        BATCH_UUID = request_data.batch_uuid

        self._register_operation(request_data)

        try:
            stock_current_info = NASDAQ.get(request_data.symbol)
            if not stock_current_info:
                self._mark_operation_error(OPERATION_UUID, BATCH_UUID)
                raise StockNotFoundError(
                    f"Stock {request_data.symbol} not found",
                    operation_uuid=OPERATION_UUID,
                )

            await asyncio.sleep(
                random.randint(settings.broker.min_delay_seconds, settings.broker.max_delay_seconds)
            )

            response = SellStockResponse(
                uuid=OPERATION_UUID,
                symbol=request_data.symbol,
                amount=quantize_money(stock_current_info.price * request_data.quantity),
                price=stock_current_info.price,
                quantity=request_data.quantity,
                batch_uuid=BATCH_UUID,
                rollback=request_data.rollback,
            )

            self._mark_operation_success(OPERATION_UUID, BATCH_UUID, response)
            return response
        except BrokerConnectionError as e:
            self._mark_operation_error(OPERATION_UUID, BATCH_UUID)
            raise BrokerConnectionError(str(e), operation_uuid=OPERATION_UUID) from e
        except Exception as e:
            self._mark_operation_error(OPERATION_UUID, BATCH_UUID)
            raise SellStockError(str(e), operation_uuid=OPERATION_UUID) from e

    async def batch_rollback(self, batch_uuid: UUID) -> bool:
        if batch_uuid not in self._batch_registry:
            logging.warning(f"Batch {batch_uuid} not found in registry")
            return False

        batch_entries : dict[UUID, BatchOperationEntry] = self._batch_registry[batch_uuid]
        successful_operations : list[BatchOperationEntry] = [
            entry
            for entry in batch_entries.values()
            if entry.state == OperationState.SUCCESS
        ]

        if not successful_operations:
            logging.info(f"No successful operations to rollback in batch {batch_uuid}")
            del self._batch_registry[batch_uuid]
            return True

        all_rollback_success = True
        max_retries = 3

        for entry in successful_operations:
            rollback_success = False

            for attempt in range(max_retries):
                try:
                    rollback_request = entry.response.to_rollback_request()

                    if isinstance(entry.response, BuyStockResponse):
                        await self.sell_stock_by_quantity(rollback_request)
                    elif isinstance(entry.response, SellStockResponse):
                        await self.buy_stock_by_quantity(rollback_request)

                    rollback_success = True
                    entry.state = OperationState.ROLLED_BACK
                    break

                except Exception as e:
                    entry.rollback_attempt = attempt + 1
                    logging.warning(
                        f"Rollback attempt {attempt + 1} failed for operation "
                        f"{entry.operation_uuid}: {e}"
                    )
                    if attempt < max_retries - 1:
                        await asyncio.sleep(settings.broker.batch_retry_delay_seconds)

            if not rollback_success:
                all_rollback_success = False
                logging.error(
                    f"Failed to rollback operation {entry.operation_uuid} "
                    f"after {max_retries} attempts"
                )

        # Clean up batch registry after rollback
        del self._batch_registry[batch_uuid]

        return all_rollback_success
