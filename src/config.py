from pydantic import BaseModel

class Settings(BaseModel):
    minimum_investment: int = 1
    retail_threshold: int = 25000

settings = Settings()