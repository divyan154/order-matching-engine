from fastapi import FastAPI,WebSocket
from src.models.order import Order
from src.services.order_book import OrderBook
from fastapi.responses import HTMLResponse
import asyncio
app = FastAPI()
clients = {
    "market": [],
    "trades": []
}
book = OrderBook(
    market_clients=clients["market"],
    trade_clients=clients["trades"]
)





@app.get("/")
def read_root():
    return {"message": "Welcome to the Order Book API"}

@app.post("/submit_order")
async def submit_order(order: Order):
    book.add_order(order)
    return {"bbo": book.get_bbo()}


@app.get("/bbo")
def get_bbo():
    return book.get_bbo()
@app.get("/orders")
def get_orders():
    return {
        "bids": _format_book(book.bids),
        "asks": _format_book(book.asks)
    }

def _format_book(book_side):
    return [
        {
            "price": price,
            "orders": [
                {
                    "order_id": entry.order_id,
                    "quantity": entry.quantity,
                    "timestamp": entry.timestamp
                }
                for entry in queue
            ]
        }
        for price, queue in book_side.items()
    ]

@app.websocket("/ws/market")
async def market_data_stream(websocket: WebSocket):
    await websocket.accept()
    book.market_clients.append(websocket)  # update the OrderBook directly
    try:
        while True:
            await websocket.receive_text()
    except:
        book.market_clients.remove(websocket)

@app.websocket("/ws/trades")
async def trade_feed_stream(websocket: WebSocket):
    await websocket.accept()
    book.trade_clients.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except:
        book.trade_clients.remove(websocket)
