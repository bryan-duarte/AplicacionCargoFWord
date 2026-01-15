from src.stock.stock import Stock
from decimal import Decimal

NASDAQ = {
    "AAPL": Stock(symbol="AAPL", price=Decimal("250")),
    "META": Stock(symbol="META", price=Decimal("150")),
    "MSFT": Stock(symbol="MSFT", price=Decimal("600")),
    "TSLA": Stock(symbol="TSLA", price=Decimal("100")),
    "AMZN": Stock(symbol="AMZN", price=Decimal("150")),
}
