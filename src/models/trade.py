from pydantic import BaseModel, Field
from uuid import uuid4
from datetime import datetime, timezone


class Trade(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    symbol: str
    price: float
    quantity: float
    buyer_id: str | None = None
    seller_id: str | None = None
    maker_order_id: str
    taker_order_id: str
    aggressor_side: str  # "buy" or "sell"
