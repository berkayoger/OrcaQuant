from typing import List

from pydantic import BaseModel, Field


class PricesModel(BaseModel):
    prices: List[float] = Field(min_length=15)
