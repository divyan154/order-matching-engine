from fastapi import APIRouter

from src.services import matching_engine

router = APIRouter(tags=["orderbook"])


@router.get("/orderbook/{symbol}")
async def get_orderbook(symbol: str, depth: int = 20):
    book = matching_engine.get_book(symbol)
    if not book:
        return {"symbol": symbol, "bids": [], "asks": [], "timestamp": None}
    return book.get_order_book_depth(depth)


@router.get("/bbo/{symbol}")
async def get_bbo(symbol: str):
    book = matching_engine.get_book(symbol)
    if not book:
        return {"symbol": symbol, "bid": None, "ask": None}
    return book.get_bbo()
