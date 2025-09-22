🚀 High-Performance Crypto Order Matching Engine
A high-performance cryptocurrency matching engine built with FastAPI that supports multiple trading symbols, real-time WebSocket streaming, and various order types (Market, Limit, IOC, FOK).

🏗️ System Architecture & Design
Key Components
FastAPI Server – Exposes HTTP and WebSocket endpoints.

OrderBook Class – Handles core matching logic per trading symbol.

In-Memory Data Structures – Enables low-latency, high-throughput matching.

WebSocket Broadcasting – Pushes live market depth and trade data to subscribed clients.




Design Principles
Symbol Isolation: Each symbol uses its own instance of OrderBook.

Async I/O: All routes use async def, allowing concurrent order submission and broadcasting.

Separation of Concerns: Models, services, and utils are cleanly organized.





📦 Data Structures
1. SortedDict (from sortedcontainers)
Stores price levels sorted by price.

Buy side: sorted in descending order (lambda x: -x)

Sell side: sorted in ascending order.

Fast retrieval of the best bid/ask.

2. deque (from collections)
Queue of orders at each price level.

Maintains FIFO for price-time priority.




⚙️ Matching Algorithm
✅ Supported Order Types
Type	Behavior
Market	Match immediately at best price
Limit	Match up to limit price, queue remainder
IOC	Match immediately, discard remaining quantity
FOK	Match fully immediately or cancel



🔁 Matching Flow
Match against opposite side of book.

For each price level:

Match as much quantity as possible.

Respect time-priority using deque.

If quantity remains:

Add to book (if order type allows).



📡 API Reference
🔹 HTTP Endpoints
Method	Route	Description
GET	/	Welcome message
POST	/submit_order	Submit a new order
GET	/bbo/{symbol}	Get best bid/ask for symbol



Sample POST Payload:


{
  "symbol": "BTCUSDT",
  "type": "limit",
  "side": "buy",
  "price": 25000,
  "quantity": 1
}



🔹 WebSocket Endpoints

/ws/market/{symbol}	Subscribe to market depth
/ws/trades/{symbol}	Subscribe to trade feed

Sample Trade Broadcast:


{
  "type": "trade",
  "data": {
    "price": 24990.5,
    "quantity": 0.5,
    "symbol": "BTCUSDT",
    "timestamp": "2025-06-16T14:32:10Z",
    "aggressor_side": "buy",
    "maker_order_id": "abc123",
    "taker_order_id": "xyz789"
  }
}



⚖️ Trade-off Decisions
Decision	Trade-offs
In-memory storage	✅ Fast, ❌ Not persistent
SortedDict + deque	✅ Efficient for matching, ❌ Higher memory usage
FastAPI with async	✅ Scalable, ❌ Requires care with shared state
No DB used	✅ Simplicity, ❌ No durability
No auth/rate-limit	✅ Easy testing, ❌ Vulnerable in prod



📈 Future Improvements
✅ Cancel & modify orders API

✅ REST endpoint for full order book

✅ User auth, sessions, and rate limiting

✅ Redis/PostgreSQL for persistent matching

✅ Admin dashboard + analytics

✅ Unit tests for order matching


🗂️ Project Structure
bash
Copy
Edit
src/
├── main.py                  # FastAPI app + routes
├── models/
│   ├── order.py             # Order schema + enums
│   ├── trade.py             # Trade schema
│   └── book_entry.py        # Internal book entry
├── services/
│   └── order_book.py        # Matching engine logic
└── utils/
    └── logger.py            # Logging config
▶️ Running the Project
1. Install dependencies

pip install -r requirements.txt
2. Start development server

uvicorn src.main:app --reload
3. Connect WebSocket client (e.g., websocat)

websocat ws://localhost:8000/ws/market/symbol





⚡ High-Level Overview of OrderBook Service
1. Purpose

The OrderBook class manages the buy and sell orders for a trading symbol (like BTC/USDT).

It matches incoming orders (market, limit, IOC, FOK).

Executes trades when conditions are met.

Broadcasts updates (market depth & trades) to WebSocket clients in real time.

2. Core Data Structures

bids (SortedDict with negative key function) → keeps buy orders sorted descending by price.

asks (SortedDict) → keeps sell orders sorted ascending by price.

deque (per price level) → maintains FIFO (first-in-first-out) order for fairness among same-price orders.

trades list → stores executed trades.

✅ This structure ensures O(log n) inserts/removals and O(1) access to best prices.

3. Order Handling

The engine supports 4 types of orders:

Market Order

Executes immediately at best available price.

Doesn’t rest on the book.

Limit Order

Executes against best opposing orders if possible.

Any unfilled quantity is added to the order book.

IOC (Immediate-or-Cancel)

Matches like a limit order.

Any leftover (unfilled) quantity is cancelled, not added to the book.

FOK (Fill-or-Kill)

Only executes if the entire order can be filled immediately.

Otherwise, it is cancelled entirely.

4. Trade Execution Flow

Add Order (add_order)

Routes to _match_market, _match_limit, or _can_fully_match.

Matches orders until filled or no more liquidity.

Records trades via _record_trade.

Record Trade (_record_trade)

Creates a Trade object (price, qty, maker/taker IDs, side).

Appends to trade history.

Broadcasts trade to trade_clients over WebSocket.

Maintain Book (_add_to_book)

If order not fully filled, adds remaining quantity to bids/asks.

Stored under the price level with FIFO queue (deque).

5. Market Data Broadcasting

Order Book Depth (broadcast_market_depth)

Builds top-N snapshot (bids/asks up to depth=10).

Sends JSON updates over WebSocket to subscribed market clients.

Trades (broadcast_trade)

Broadcasts trade execution events in real time to trade clients.

✅ This makes the engine usable for real-time trading UIs or IoT clients (which fits Grid OS’s IoT theme).

6. Best Bid/Offer (BBO)

get_bbo() returns best bid (highest buy) and best ask (lowest sell).

Useful for market-making and UI displays.

7. Scalability / Efficiency

Uses SortedDict → ensures order prices are always sorted.

Uses deque → O(1) FIFO execution within price levels.

Async functions (async def) → multiple clients handled concurrently via WebSockets.
