"""Decimal utility functions for quantizing values to specific precisions."""

from decimal import ROUND_HALF_UP, Decimal

from src.config.config import settings

_QUANTIZER_MONEY = Decimal(f"0.{'0' * settings.shared.money_decimal_precision}")
_QUANTIZER_QUANTITY = Decimal(f"0.{'0' * settings.shared.quantity_decimal_precision}")
_QUANTIZER_PERCENTAGE = Decimal(
    f"0.{'0' * settings.shared.percentage_decimal_precision}"
)


def quantize_money(value: Decimal) -> Decimal:
    """Quantize a Decimal value to MONEY precision (2 decimal places)."""
    if not isinstance(value, Decimal):
        value = Decimal(str(value))
    return value.quantize(_QUANTIZER_MONEY, rounding=ROUND_HALF_UP)


def quantize_quantity(value: Decimal) -> Decimal:
    """Quantize a Decimal value to QUANTITY precision (9 decimal places)."""
    if not isinstance(value, Decimal):
        value = Decimal(str(value))
    return value.quantize(_QUANTIZER_QUANTITY, rounding=ROUND_HALF_UP)


def quantize_percentage(value: Decimal) -> Decimal:
    """Quantize a Decimal value to PERCENTAGE precision (4 decimal places)."""
    if not isinstance(value, Decimal):
        value = Decimal(str(value))
    return value.quantize(_QUANTIZER_PERCENTAGE, rounding=ROUND_HALF_UP)
