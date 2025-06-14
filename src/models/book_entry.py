from pydantic import BaseModel
from datetime import datetime


class OrderBookEntry(BaseModel):
    order_id: str
    quantity: float
    timestamp: datetime
