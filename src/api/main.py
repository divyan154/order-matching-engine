import json
import socket
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.services import db, matching_engine
from src.models.trade import Trade
from src.services.order_book import OrderBook
from src.utils.logger import logger
from src.api.routes import orders, orderbook, trades, auth


# ---------------------------------------------------------------------------
# Broadcast callbacks (injected into matching_engine)
# ---------------------------------------------------------------------------

async def _broadcast_trade(trade: Trade):
    symbol = trade.symbol
    book = matching_engine.get_book(symbol)
    if not book:
        return
    message = json.dumps({
        "type": "trade",
        "data": {
            "id": trade.id,
            "price": trade.price,
            "quantity": trade.quantity,
            "symbol": trade.symbol,
            "timestamp": trade.timestamp.isoformat() + "Z",
            "aggressor_side": trade.aggressor_side,
            "maker_order_id": trade.maker_order_id,
            "taker_order_id": trade.taker_order_id,
        },
    }, default=str)
    dead = []
    for ws in book.trade_clients:
        try:
            await ws.send_text(message)
        except Exception:
            dead.append(ws)
    for ws in dead:
        book.trade_clients.remove(ws)


async def _broadcast_depth(book: OrderBook):
    snapshot = book.get_order_book_depth()
    message = json.dumps({"type": "market_depth", "data": snapshot})
    dead = []
    for ws in book.market_clients:
        try:
            await ws.send_text(message)
        except Exception:
            dead.append(ws)
    for ws in dead:
        book.market_clients.remove(ws)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    # DNS debug — logs before DB connection attempt
    db_url = db.settings.database_url
    # Extract hostname from URL for DNS check
    try:
        host = db_url.split("@")[1].split(":")[0].split("/")[0]
        print(f"[DNS] Resolving host: {host}")
        result = socket.getaddrinfo(host, 5432)
        print(f"[DNS] Resolution succeeded: {result[0]}")
    except Exception as e:
        print(f"[DNS] Resolution FAILED: {e}")

    # Connect to DB
    await db.init_db()
    logger.info("[Startup] Database pool initialized")

    # Register WS broadcast callbacks into the matching engine
    matching_engine.register_broadcast_callbacks(_broadcast_trade, _broadcast_depth)

    yield

    logger.info("[Shutdown] Closing database pool")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(title="Order Matching Engine", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://order-engine-frontend-production.up.railway.app"],  # tighten in production
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

# Routers
app.include_router(auth.router)
app.include_router(orders.router)
app.include_router(orderbook.router)
app.include_router(trades.router)


# ---------------------------------------------------------------------------
# Legacy + utility routes
# ---------------------------------------------------------------------------

@app.get("/")
def read_root():
    return {"message": "Order Matching Engine", "docs": "/docs"}


@app.get("/dashboard")
async def serve_dashboard():
    return FileResponse("static/index.html")


# ---------------------------------------------------------------------------
# WebSocket endpoints
# ---------------------------------------------------------------------------

@app.websocket("/ws/market/{symbol}")
async def market_data_stream(websocket: WebSocket, symbol: str):
    await websocket.accept()
    # Lazily create the book so WS clients can connect before any order is placed
    book = matching_engine._get_or_create(symbol)[1]
    book.market_clients.append(websocket)
    logger.info(f"[WS] Market client connected: {symbol}")
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in book.market_clients:
            book.market_clients.remove(websocket)


@app.websocket("/ws/trades/{symbol}")
async def trade_feed_stream(websocket: WebSocket, symbol: str):
    await websocket.accept()
    book = matching_engine._get_or_create(symbol)[1]
    book.trade_clients.append(websocket)
    logger.info(f"[WS] Trade client connected: {symbol}")
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in book.trade_clients:
            book.trade_clients.remove(websocket)
