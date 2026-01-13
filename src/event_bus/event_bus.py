import asyncio
from enum import Enum
from datetime import datetime
from typing import Callable
import logging
from pydantic import BaseModel, Field
from src.config.config import settings
from src.portfolio.portfolio_register import portfolio_registry
from decimal import Decimal
from src.event_bus.event_dtos import EventType


class AsyncEventBus:
    def __init__(self):
        self._listeners = {}

    def subscribe(self, event_type: EventType, callback: Callable):
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(callback)

    async def emit(self, event_type: EventType, event_data: BaseModel):
        if event_type in self._listeners:
            tasks = [callback(event_data) for callback in self._listeners[event_type]]
            await asyncio.gather(*tasks)


bus = AsyncEventBus()
