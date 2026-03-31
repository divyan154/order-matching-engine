from fastapi import APIRouter

from src.services import db

router = APIRouter(tags=["trades"])


@router.get("/trades/{symbol}")
async def get_trades(symbol: str, limit: int = 50):
    return await db.get_trades_for_symbol(symbol, limit)
