from fastapi import FastAPI
from src.models.order import Order
from src.services.order_book import OrderBook

app = FastAPI()
book = OrderBook()


@app.get("/")
def read_root():
    return {"message": "Welcome to the Order Book API"}

@app.post("/order")
def place_order(order: Order):
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