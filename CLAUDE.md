## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server (auto-reload)
uvicorn src.api.main:app --reload

# Run production server
uvicorn src.api.main:app --host 0.0.0.0 --port 8000

# Run integration tests (server must be running at localhost:8000)
pytest tests/test_integration.py -v

# Run a single test
pytest tests/test_integration.py::test_function_name -v
```

## Environment

Copy `.env.example` to `.env` and fill in:
- `DATABASE_URL` — asyncpg-compatible PostgreSQL URL (Supabase)
- `JWT_SECRET` — random secret for JWT signing

## Architecture

The engine is built around **in-memory matching with async serialization per symbol**.

### Request lifecycle (order submission)

```
POST /orders
  → create Order + insert to DB (status=OPEN)
  → matching_engine.submit_order()
      → enqueue OrderTask onto per-symbol asyncio.Queue
      → await asyncio.Future (blocks HTTP response)
  → worker dequeues, calls OrderBook.match() (sync, no I/O)
  → persist trades + update order statuses in DB
  → WebSocket broadcast (fire-and-forget)
  → resolve Future → HTTP response with trades
```

### Key design decisions

- **Per-symbol isolation**: each symbol has its own `OrderBook`, `asyncio.Queue`, and worker task. No cross-symbol locking needed.
- **Sync matching core**: `OrderBook.match()` is pure Python with no I/O, keeping matching latency low. The async wrapper in `MatchingEngine` handles DB and broadcast.
- **In-memory order book**: `SortedDict` (bids descending, asks ascending) with a `deque` at each price level for FIFO. `_order_index` dict enables O(1) cancel.
- **DB durability**: open orders are recovered from DB on startup via `restore_symbol()`, rebuilding the in-memory book after a restart.
- **Broadcast decoupling**: WebSocket callbacks are injected into `MatchingEngine` from `main.py` via `set_broadcast_callback()` / `set_trade_callback()` to avoid circular imports.

### Order types

| Type | Behaviour |
|------|-----------|
| LIMIT | Rest on book at price if not immediately matched |
| MARKET | Match against best available; cancel remainder |
| IOC | Match what's available immediately, cancel rest |
| FOK | Match full quantity immediately or cancel entirely |

### Service layer

| File | Responsibility |
|------|----------------|
| `src/services/order_book.py` | Pure in-memory matching; no async, no DB calls |
| `src/services/matching_engine.py` | Async orchestration: queue, DB persistence, WS broadcast |
| `src/services/db.py` | asyncpg pool; all SQL lives here |
| `src/utils/config.py` | Pydantic settings loaded from `.env` |

### WebSocket endpoints

- `GET /ws/market/{symbol}` — streams order book depth snapshots on each match
- `GET /ws/trades/{symbol}` — streams individual trade events on execution
