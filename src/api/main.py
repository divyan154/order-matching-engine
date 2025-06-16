from fastapi import FastAPI,WebSocket, WebSocketDisconnect
from src.models.order import Order
from src.services.order_book import OrderBook
from fastapi.responses import HTMLResponse
from fastapi import HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from src.utils.logger import logger

app = FastAPI()
clients = {
    "market": [],
    "trades": []
}


# Mount the static directory
app.mount("/static", StaticFiles(directory="static"), name="static")


books = {}  # Dictionary to hold multiple OrderBooks by symbol
def get_or_create_book(symbol: str) -> OrderBook:
    if symbol not in books:
        books[symbol] = OrderBook(symbol,clients["market"], clients["trades"])
    return books[symbol]

@app.get("/")
def read_root():
    return {"message": "Welcome to the Order Book API"}

@app.get("/dashboard")
async def serve_dashboard():
    return FileResponse("static/index.html")

@app.post("/submit_order")
async def submit_order(order: Order):
    try:
        book = get_or_create_book(order.symbol)
        await book.add_order(order)
        return {"bbo": book.get_bbo()}
    except Exception as e:
        logger.error(f"Order submission failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/bbo/{symbol}")
def get_bbo(symbol: str):
    book = get_or_create_book(symbol)
    return book.get_bbo()

@app.websocket("/ws/market/{symbol}")
async def market_data_stream(websocket: WebSocket, symbol: str):
    await websocket.accept()
    book = get_or_create_book(symbol)
    book.market_clients.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        book.market_clients.remove(websocket)
        # logger.info(f"[WebSocket] Market client disconnected for {symbol}")

@app.websocket("/ws/trades/{symbol}")
async def trade_feed_stream(websocket: WebSocket, symbol: str):
    await websocket.accept()
    book = get_or_create_book(symbol)
    book.trade_clients.append(websocket)
    # logger.info(f"[WebSocket] Trade client connected for symbol: {symbol}")
    # logger.info(f"[WebSocket] Total trade_clients: {len(book.trade_clients)}")

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        book.trade_clients.remove(websocket)
        # logger.info(f"[WebSocket] Trade client disconnected for {symbol}")

