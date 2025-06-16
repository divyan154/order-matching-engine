from pydantic import BaseModel
from uuid import uuid4
from enum import Enum
from datetime import datetime


class Side(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    LIMIT = "limit"
    MARKET = "market"
    IOC='ioc' # Immediate or Cancel (partial fill allowed, rest cancelled)
    FOK='fok' # Fill or Kill (must be fully filled, otherwise cancelled)

class Order(BaseModel):
    id: str = str(uuid4())
    timestamp: datetime = datetime.utcnow()
    symbol: str
    side: Side
    type: OrderType
    price: float = 0.0  # Only for LIMIT
    quantity: float
