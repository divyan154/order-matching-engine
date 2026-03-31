"""
Integration tests for the Order Matching Engine.

Requires the server to be running at http://localhost:8000
with a live Supabase DB connection.

Run with:
    pytest tests/test_integration.py -v
"""

import pytest
import httpx

BASE_URL = "http://localhost:8000"


@pytest.fixture(scope="module")
def client():
    with httpx.Client(base_url=BASE_URL, timeout=10) as c:
        yield c


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

def test_root(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "Order Matching Engine" in r.json()["message"]


def test_docs_accessible(client):
    r = client.get("/docs")
    assert r.status_code == 200


# ---------------------------------------------------------------------------
# Order book — empty symbol
# ---------------------------------------------------------------------------

def test_orderbook_empty_symbol(client):
    r = client.get("/orderbook/XYZUSDT")
    assert r.status_code == 200
    data = r.json()
    assert data["bids"] == []
    assert data["asks"] == []


def test_bbo_empty_symbol(client):
    r = client.get("/bbo/XYZUSDT")
    assert r.status_code == 200
    data = r.json()
    assert data["bid"] is None
    assert data["ask"] is None


# ---------------------------------------------------------------------------
# Limit order — resting (no cross)
# ---------------------------------------------------------------------------

def test_limit_order_rests_in_book(client):
    r = client.post("/orders", json={
        "symbol": "TESTUSDT", "side": "sell", "type": "limit",
        "price": 100.0, "quantity": 1.0
    })
    assert r.status_code == 201
    data = r.json()
    assert data["trades_executed"] == 0

    # Should appear in asks
    book = client.get("/orderbook/TESTUSDT").json()
    assert len(book["asks"]) > 0
    assert book["asks"][0][0] == "100.0"


# ---------------------------------------------------------------------------
# Limit order — full cross (both sides fully filled)
# ---------------------------------------------------------------------------

def test_limit_order_full_cross(client):
    # Place resting sell
    r = client.post("/orders", json={
        "symbol": "BTCUSDT", "side": "sell", "type": "limit",
        "price": 50000.0, "quantity": 0.5
    })
    assert r.status_code == 201
    sell_id = r.json()["order_id"]

    # Cross with buy
    r = client.post("/orders", json={
        "symbol": "BTCUSDT", "side": "buy", "type": "limit",
        "price": 50000.0, "quantity": 0.5
    })
    assert r.status_code == 201
    data = r.json()
    assert data["trades_executed"] == 1
    trade = data["trades"][0]
    assert trade["price"] == 50000.0
    assert trade["quantity"] == 0.5

    # Sell order status in DB → filled
    sell_order = client.get(f"/orders/{sell_id}").json()
    assert sell_order["status"] == "filled"
    assert float(sell_order["remaining_qty"]) == 0.0


# ---------------------------------------------------------------------------
# GET /orders/{id} — not found
# ---------------------------------------------------------------------------

def test_get_order_not_found(client):
    r = client.get("/orders/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# GET /trades/{symbol}
# ---------------------------------------------------------------------------

def test_get_trades_returns_list(client):
    r = client.get("/trades/BTCUSDT")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


# ---------------------------------------------------------------------------
# Cancel order
# ---------------------------------------------------------------------------

def test_cancel_open_order(client):
    r = client.post("/orders", json={
        "symbol": "BTCUSDT", "side": "buy", "type": "limit",
        "price": 40000.0, "quantity": 1.0
    })
    assert r.status_code == 201
    order_id = r.json()["order_id"]

    r = client.delete(f"/orders/{order_id}")
    assert r.status_code == 200
    result = r.json()
    assert result["cancelled"] is True
    assert result["removed_from_book"] is True

    # Status in DB → cancelled
    order = client.get(f"/orders/{order_id}").json()
    assert order["status"] == "cancelled"

    # Should be gone from bids
    book = client.get("/orderbook/BTCUSDT").json()
    bid_prices = [b[0] for b in book["bids"]]
    assert "40000.0" not in bid_prices


def test_cancel_filled_order_returns_400(client):
    # Place + cross to fill
    r = client.post("/orders", json={
        "symbol": "BTCUSDT", "side": "sell", "type": "limit",
        "price": 50000.0, "quantity": 0.1
    })
    sell_id = r.json()["order_id"]
    client.post("/orders", json={
        "symbol": "BTCUSDT", "side": "buy", "type": "limit",
        "price": 50000.0, "quantity": 0.1
    })

    r = client.delete(f"/orders/{sell_id}")
    assert r.status_code == 400


def test_cancel_nonexistent_order_returns_404(client):
    r = client.delete("/orders/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Market order
# ---------------------------------------------------------------------------

def test_market_order_fills_against_book(client):
    # Seed the book with a sell
    client.post("/orders", json={
        "symbol": "BTCUSDT", "side": "sell", "type": "limit",
        "price": 51000.0, "quantity": 0.2
    })

    r = client.post("/orders", json={
        "symbol": "BTCUSDT", "side": "buy", "type": "market",
        "price": 0.0, "quantity": 0.2
    })
    assert r.status_code == 201
    data = r.json()
    assert data["trades_executed"] == 1
    assert data["trades"][0]["price"] == 51000.0


def test_market_order_no_liquidity(client):
    # No sells in EMPTYUSDT book
    r = client.post("/orders", json={
        "symbol": "EMPTYUSDT", "side": "buy", "type": "market",
        "price": 0.0, "quantity": 1.0
    })
    assert r.status_code == 201
    assert r.json()["trades_executed"] == 0


# ---------------------------------------------------------------------------
# IOC order
# ---------------------------------------------------------------------------

def test_ioc_partial_fill(client):
    # Seed 1.0 sell
    client.post("/orders", json={
        "symbol": "ETHUSDT", "side": "sell", "type": "limit",
        "price": 3000.0, "quantity": 1.0
    })

    # IOC buy for 5.0 — only 1.0 available
    r = client.post("/orders", json={
        "symbol": "ETHUSDT", "side": "buy", "type": "ioc",
        "price": 3000.0, "quantity": 5.0
    })
    assert r.status_code == 201
    data = r.json()
    assert data["trades_executed"] == 1
    assert data["trades"][0]["quantity"] == 1.0

    # Remainder not added to bids
    book = client.get("/orderbook/ETHUSDT").json()
    assert book["bids"] == []


def test_ioc_no_match_cancels_entirely(client):
    r = client.post("/orders", json={
        "symbol": "ETHUSDT", "side": "buy", "type": "ioc",
        "price": 1000.0, "quantity": 1.0  # below any ask
    })
    assert r.status_code == 201
    assert r.json()["trades_executed"] == 0


# ---------------------------------------------------------------------------
# FOK order
# ---------------------------------------------------------------------------

def test_fok_full_fill(client):
    # Seed enough sell liquidity
    client.post("/orders", json={
        "symbol": "BNBUSDT", "side": "sell", "type": "limit",
        "price": 300.0, "quantity": 2.0
    })

    r = client.post("/orders", json={
        "symbol": "BNBUSDT", "side": "buy", "type": "fok",
        "price": 300.0, "quantity": 2.0
    })
    assert r.status_code == 201
    data = r.json()
    assert data["trades_executed"] == 1
    assert data["trades"][0]["quantity"] == 2.0


def test_fok_insufficient_liquidity_cancels(client):
    r = client.post("/orders", json={
        "symbol": "XRPUSDT", "side": "buy", "type": "fok",
        "price": 1.0, "quantity": 100.0
    })
    assert r.status_code == 201
    data = r.json()
    assert data["trades_executed"] == 0

    # Nothing should be in bids either
    book = client.get("/orderbook/XRPUSDT").json()
    assert book["bids"] == []


# ---------------------------------------------------------------------------
# Partial fill — limit order
# ---------------------------------------------------------------------------

def test_limit_order_partial_fill(client):
    # Seed 0.3 sell
    client.post("/orders", json={
        "symbol": "SOLUSDT", "side": "sell", "type": "limit",
        "price": 150.0, "quantity": 0.3
    })

    # Buy 1.0 — only 0.3 fills, rest rests in book
    r = client.post("/orders", json={
        "symbol": "SOLUSDT", "side": "buy", "type": "limit",
        "price": 150.0, "quantity": 1.0
    })
    assert r.status_code == 201
    data = r.json()
    assert data["trades_executed"] == 1
    assert data["trades"][0]["quantity"] == 0.3

    # Remaining 0.7 should be in bids
    book = client.get("/orderbook/SOLUSDT").json()
    assert len(book["bids"]) > 0
    remaining = float(book["bids"][0][1])
    assert abs(remaining - 0.7) < 0.0001
