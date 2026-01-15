"""Event bus errors."""

from pydantic import ValidationError


class EventBusError(Exception):
    """Base error for event bus."""

    pass


class EventValidationError(EventBusError):
    """Raised when event data fails Pydantic schema validation."""

    def __init__(self, validation_error: ValidationError):
        self.validation_error = validation_error
        super().__init__(f"Event validation failed: {validation_error}")
