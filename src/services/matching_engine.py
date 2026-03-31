"""
Per-symbol asyncio.Queue + asyncio.Lock + worker task.

Flow:
  POST /orders
    → insert to DB (open)
    → submit_order() enqueues an OrderTask with a Future
    → HTTP handler awaits the Future
    → worker dequeues, runs match(), writes trades to DB, broadcasts WS
    → worker sets Future result → handler returns response
"""

import asyncio
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from src.models.order import Order
from src.models.trade import Trade
from src.utils.logger import logger

if TYPE_CHECKING:
    from src.services.order_book import OrderBook


@dataclass
class OrderTask:
    order: Order
    future: asyncio.Future


# Per-symbol state
_queues: dict[str, asyncio.Queue] = {}
_books: dict[str, "OrderBook"] = {}
_workers: dict[str, asyncio.Task] = {}

# Callbacks set by main.py so the engine can broadcast without importing FastAPI
_broadcast_trade_cb = None
_broadcast_depth_cb = None


def register_broadcast_callbacks(trade_cb, depth_cb):
    global _broadcast_trade_cb, _broadcast_depth_cb
    _broadcast_trade_cb = trade_cb
    _broadcast_depth_cb = depth_cb


def get_book(symbol: str) -> "OrderBook | None":
    return _books.get(symbol)


def _get_or_create(symbol: str) -> tuple[asyncio.Queue, "OrderBook"]:
    if symbol not in _queues:
        from src.services.order_book import OrderBook
        _queues[symbol] = asyncio.Queue()
        _books[symbol] = OrderBook(symbol)
        _workers[symbol] = asyncio.create_task(
            _worker(symbol), name=f"worker-{symbol}"
        )
        logger.info(f"[Engine] Created worker for symbol: {symbol}")
    return _queues[symbol], _books[symbol]


async def _worker(symbol: str):
    """Single worker per symbol — serializes all matching for that symbol."""
    queue = _queues[symbol]
    book = _books[symbol]

    while True:
        task: OrderTask = await queue.get()
        try:
            trades = await _process(book, task.order)
            task.future.set_result(trades)
        except Exception as e:
            logger.error(f"[Worker:{symbol}] error: {e}", exc_info=True)
            if not task.future.done():
                task.future.set_exception(e)
        finally:
            queue.task_done()


async def _process(book: "OrderBook", order: Order) -> list[Trade]:
    from src.services import db

    trades = book.match(order)

    # Track how much was filled per maker order
    maker_filled: dict[str, float] = {}
    for trade in trades:
        maker_filled[trade.maker_order_id] = maker_filled.get(trade.maker_order_id, 0) + trade.quantity

    # Persist trades
    for trade in trades:
        await db.insert_trade({
            "id": trade.id,
            "symbol": trade.symbol,
            "price": trade.price,
            "quantity": trade.quantity,
            "buyer_id": trade.buyer_id,
            "seller_id": trade.seller_id,
            "timestamp": trade.timestamp,
        })
        if _broadcast_trade_cb:
            asyncio.create_task(_broadcast_trade_cb(trade))

    # Update maker orders in DB
    for maker_id, filled_qty in maker_filled.items():
        maker_row = await db.get_order_by_id(maker_id)
        if maker_row:
            new_remaining = float(maker_row["remaining_qty"]) - filled_qty
            new_remaining = max(new_remaining, 0.0)
            new_status = "filled" if new_remaining <= 0 else "partial"
            await db.update_order(maker_id, new_status, new_remaining)

    # Update incoming order status in DB
    filled = order.quantity - order.remaining_qty
    if order.remaining_qty <= 0:
        status = "filled"
    elif filled > 0:
        status = "partial"
    else:
        status = order.status.value

    await db.update_order(order.id, status, order.remaining_qty)

    if _broadcast_depth_cb:
        asyncio.create_task(_broadcast_depth_cb(book))

    return trades


async def submit_order(order: Order) -> list[Trade]:
    """Enqueue order and wait for matching result."""
    queue, _ = _get_or_create(order.symbol)
    loop = asyncio.get_running_loop()
    future = loop.create_future()
    await queue.put(OrderTask(order=order, future=future))
    return await future


async def restore_symbol(symbol: str):
    """Load open/partial orders from DB into in-memory book on startup."""
    from src.services import db
    _, book = _get_or_create(symbol)
    orders = await db.get_open_orders_for_symbol(symbol)
    for row in orders:
        order = Order(
            id=str(row["id"]),
            user_id=str(row["user_id"]) if row["user_id"] else None,
            symbol=row["symbol"],
            side=row["side"],
            type=row["type"],
            price=float(row["price"]) if row["price"] else 0.0,
            quantity=float(row["quantity"]),
            remaining_qty=float(row["remaining_qty"]),
            status=row["status"],
            timestamp=row["created_at"],
        )
        book.restore_order(order)
    logger.info(f"[Engine] Restored {len(orders)} open orders for {symbol}")
