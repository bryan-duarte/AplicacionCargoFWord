
class BrokerError(Exception):
    pass

class BuyStockError(BrokerError):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class SellStockError(BrokerError):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)