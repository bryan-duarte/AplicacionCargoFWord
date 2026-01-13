from pydantic import BaseModel
from decimal import Decimal


class Settings(BaseModel):
    minimum_investment: int = 1
    retail_threshold: int = 25000
    balance_threshold: Decimal = Decimal("0.00")
    stock_price_change_threshold: Decimal = Decimal("0.00")


settings = Settings()
