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
