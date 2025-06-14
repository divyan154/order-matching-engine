from pydantic import BaseModel
from datetime import datetime
from uuid import uuid4


class Trade(BaseModel):
    id: str = str(uuid4())
    timestamp: datetime = datetime.utcnow()
    price: float
    quantity: float
    buy_order_id: str
    sell_order_id: str
