import pytest
import asyncio
import time
from datetime import datetime, timezone
import uuid
import os, sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.services.order_book import OrderBook
from src.models.order import Order, OrderType, Side


def make_order(side=Side.BUY, price=100.0, quantity=1.0):
    return Order(
        id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc),
        symbol="BTCUSDT",
        type=OrderType.LIMIT,
        side=side,
        price=price,
        quantity=quantity,
    )


@pytest.mark.asyncio
async def test_benchmark():
    order_count = 5000  # You can change this value to test different loads
    book = OrderBook(symbol="BTCUSDT")
    orders = [make_order() for _ in range(order_count)]

    start = time.time()
    await asyncio.gather(*(book.add_order(order) for order in orders))
    end = time.time()

    elapsed = end - start
    ops = order_count / elapsed

    print(f"\n⏱️ Benchmark Results:")
    print(f"  • Total Orders: {order_count}")
    print(f"  • Time Elapsed: {elapsed:.4f} seconds")
    print(f"  • Orders per Second: {ops:.2f}\n")

    # Optional: Disable this assert temporarily to always see results
    assert ops > 1000, "Throughput is below expected threshold (1000 orders/sec)"
