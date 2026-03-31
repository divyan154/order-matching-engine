from pydantic import BaseModel, Field
from uuid import uuid4
from enum import Enum
from datetime import datetime, timezone


class Side(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    LIMIT = "limit"
    MARKET = "market"
    IOC = "ioc"
    FOK = "fok"


class OrderStatus(str, Enum):
    OPEN = "open"
    PARTIAL = "partial"
    FILLED = "filled"
    CANCELLED = "cancelled"


class OrderCreate(BaseModel):
    """What the client sends."""
    symbol: str
    side: Side
    type: OrderType
    price: float = 0.0
    quantity: float


class Order(BaseModel):
    """Internal order model."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    user_id: str | None = None
    symbol: str
    side: Side
    type: OrderType
    price: float = 0.0
    quantity: float
    remaining_qty: float = 0.0
    status: OrderStatus = OrderStatus.OPEN

    def model_post_init(self, __context):
        if self.remaining_qty == 0.0:
            self.remaining_qty = self.quantity
