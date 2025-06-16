from pydantic import BaseModel
from uuid import UUID, uuid4
from datetime import datetime,timezone

class Trade(BaseModel):
    id:str = str(uuid4())
    timestamp: datetime = datetime.now(timezone.utc)
    symbol: str
    price: float
    quantity: float
    maker_id: UUID
    taker_id: UUID
    aggressor_side: str  # "buy" or "sell"
