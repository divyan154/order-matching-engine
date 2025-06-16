import pytest
from src.models.order import Order, Side, OrderType
from src.services.order_book import OrderBook

@pytest.mark.asyncio
async def test_limit_order_adds_to_book():
    book = OrderBook("BTCUSDT")
    order = Order(
        id="order1",
        symbol="BTCUSDT",
        side=Side.BUY,
        price=25000,
        quantity=1,
        type=OrderType.LIMIT
    )

    await book.add_order(order)

    assert 25000 in book.bids
    assert len(book.bids[25000]) == 1
    assert book.bids[25000][0].quantity == 1

@pytest.mark.asyncio
async def test_market_order_does_not_add_to_book():
    book = OrderBook("BTCUSDT")
    market_order = Order(
        id="market1",
        symbol="BTCUSDT",
        side=Side.SELL,
        quantity=1,
        type=OrderType.MARKET
    )

    await book.add_order(market_order)

    # Market orders should not be added to the book
    assert not book.asks and not book.bids

@pytest.mark.asyncio
async def test_ioc_order_partial_fill_and_cancel():
    book = OrderBook("BTCUSDT")

    # Add a resting BUY order
    resting_order = Order(
        
        symbol="BTCUSDT",
        side=Side.BUY,
        price=25000,
        quantity=1,
        type=OrderType.LIMIT
    )
    await book.add_order(resting_order)

    # IOC order to SELL partially matches and remainder cancels
    ioc_order = Order(
        
        symbol="BTCUSDT",
        side=Side.SELL,
        price=25000,
        quantity=2,
        type=OrderType.IOC
    )
    await book.add_order(ioc_order)

    # Should not exist in book after
    assert 25000 not in book.asks

@pytest.mark.asyncio
async def test_fok_order_cancels_if_not_fully_matchable():
    book = OrderBook("BTCUSDT")

    # Add small BUY order
    await book.add_order(Order(
        id="limit2",
        symbol="BTCUSDT",
        side=Side.BUY,
        price=25000,
        quantity=1,
        type=OrderType.LIMIT
    ))

    # FOK order to SELL 5 — should cancel because not fully matchable
    fok_order = Order(
        id="fok1",
        symbol="BTCUSDT",
        side=Side.SELL,
        price=25000,
        quantity=5,
        type=OrderType.FOK
    )
    await book.add_order(fok_order)

    # Book should remain unchanged
    assert 25000 in book.bids
    assert book.bids[25000][0].quantity == 1
