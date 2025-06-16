from pydantic import BaseModel
from uuid import UUID, uuid4
from datetime import datetime,timezone

class Trade(BaseModel):
    id: UUID = uuid4()
    timestamp: datetime = datetime.now(timezone.utc)
    symbol: str
    price: float
    quantity: float
    buy_order_id: UUID
    sell_order_id: UUID
    maker_id: UUID
    taker_id: UUID
    aggressor_side: str  # "buy" or "sell"
