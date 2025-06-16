import asyncio
import pytest
from datetime import datetime, timezone
import uuid
import sys
import os

# Add src path to sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.services.order_book import OrderBook
from src.models.order import Order, OrderType, Side

# ✅ Helper function to create a single test order
def make_order(**kwargs):
    return Order(
        id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc),
        symbol=kwargs.get("symbol", "BTCUSDT"),
        type=kwargs.get("type", OrderType.LIMIT),
        side=kwargs.get("side", Side.BUY),
        price=kwargs.get("price", 100.0),
        quantity=kwargs.get("quantity", 1.0),
    )

def make_multiple_orders():
    return [
        make_order(type=OrderType.LIMIT, side=Side.BUY, price=150.0),
        make_order(type=OrderType.LIMIT, side=Side.SELL, price=50.0),
        make_order(type=OrderType.LIMIT, side=Side.BUY, price=100.0),
        make_order(type=OrderType.LIMIT, side=Side.SELL, price=200.0),
    ]

@pytest.mark.asyncio
async def test_limit_order_matching():
    book = OrderBook(symbol="BTCUSDT")

    sell_order = make_order(side=Side.SELL, type=OrderType.LIMIT, price=100.0, quantity=1.0)
    buy_order = make_order(side=Side.BUY, type=OrderType.MARKET, price=100.0, quantity=1.0)

    await book.add_order(sell_order)
    await book.add_order(buy_order)

    assert len(book.trades) == 1
    trade = book.trades[0]
    assert trade.price == 100.0
    assert trade.quantity == 1.0


@pytest.mark.asyncio
async def test_fok_order_rejected_when_not_fully_matchable():
    book = OrderBook(symbol="BTCUSDT")
    sell_order = make_order(side=Side.SELL, type=OrderType.LIMIT, price=100.0, quantity=2.0)
    fok_order = make_order(type=OrderType.FOK, side=Side.BUY, price=100.0, quantity=5.0)
    await book.add_order(sell_order)
    await book.add_order(fok_order)
    
    assert len(book.trades) == 0
    assert len(book.asks) == 1  # Should not add to book


@pytest.mark.asyncio
async def test_ioc_partial_fill():
    book = OrderBook(symbol="BTCUSDT")

    sell_order = make_order(side=Side.SELL, type=OrderType.LIMIT, price=100.0, quantity=2.0)
    await book.add_order(sell_order)

    ioc_order = make_order(type=OrderType.IOC, side=Side.BUY, price=100.0, quantity=5.0)
    await book.add_order(ioc_order)

    assert len(book.trades) == 1
    assert book.trades[0].quantity == 2.0
    assert len(book.bids) == 0


@pytest.mark.asyncio
async def test_order_book_depth():
    book = OrderBook(symbol="BTCUSDT")

    order1 = make_order(price=100.0, quantity=2.0)
    order2 = make_order(price=99.5, quantity=3.0)
    await book.add_order(order1)
    await book.add_order(order2)

    depth = book.get_order_book_depth()
    assert len(depth["bids"]) == 2
    assert depth["bids"][0][0] == "100.0"
    assert depth["bids"][0][1] == "2.0"


@pytest.mark.asyncio
async def test_market_order_execution():
    book = OrderBook(symbol="BTCUSDT")

    sell_order = make_order(side=Side.SELL, type=OrderType.LIMIT, price=100.0, quantity=1.0)
    await book.add_order(sell_order)

    market_order = make_order(type=OrderType.MARKET, side=Side.BUY, quantity=1.0)
    await book.add_order(market_order)

    assert len(book.trades) == 1
    assert book.trades[0].price == 100.0
    assert book.trades[0].quantity == 1.0
@pytest.mark.asyncio
async def test_price_time_priority():
    book = OrderBook(symbol="BTCUSDT")

    # First limit sell at price 100.0, quantity 1.0
    sell_order_1 = Order(
        id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc),
        symbol="BTCUSDT",
        type=OrderType.LIMIT,
        side=Side.SELL,
        price=100.0,
        quantity=1.0,
    )
    await book.add_order(sell_order_1)

    # Second limit sell at same price 100.0, quantity 1.0, after slight delay
    await asyncio.sleep(0.01)  # Ensure different timestamps
    sell_order_2 = Order(
        id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc),
        symbol="BTCUSDT",
        type=OrderType.LIMIT,
        side=Side.SELL,
        price=100.0,
        quantity=1.0,
    )
    await book.add_order(sell_order_2)

    # Market buy order for quantity 1.0 — should match with sell_order_1
    buy_order = Order(
        id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc),
        symbol="BTCUSDT",
        type=OrderType.MARKET,
        side=Side.BUY,
        quantity=1.0,
    )
    await book.add_order(buy_order)

    # Assert trade occurred with first order
    assert len(book.trades) == 1
    trade = book.trades[0]
    assert str(trade.sell_order_id) == sell_order_1.id
