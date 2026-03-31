import asyncpg
from datetime import datetime, timezone
from src.utils.config import settings


def _naive_utc(dt: datetime) -> datetime:
    """Strip timezone info — DB columns are TIMESTAMP (no tz)."""
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt

_pool: asyncpg.Pool = None


async def init_db():
    global _pool
    _pool = await asyncpg.create_pool(
        settings.database_url,
        min_size=2,
        max_size=10,
        ssl="require",
    )


async def get_pool() -> asyncpg.Pool:
    return _pool


# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------

async def insert_order(order_data: dict) -> dict:
    async with _pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO orders (id, user_id, symbol, side, type, price, quantity, remaining_qty, status, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            RETURNING *
            """,
            order_data["id"],
            order_data.get("user_id"),
            order_data["symbol"],
            order_data["side"],
            order_data["type"],
            order_data["price"],
            order_data["quantity"],
            order_data["remaining_qty"],
            order_data["status"],
            _naive_utc(order_data["timestamp"]),
        )
        return dict(row)


async def get_order_by_id(order_id: str) -> dict | None:
    async with _pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM orders WHERE id = $1", order_id)
        return dict(row) if row else None


async def update_order(order_id: str, status: str, remaining_qty: float) -> None:
    async with _pool.acquire() as conn:
        await conn.execute(
            "UPDATE orders SET status = $1, remaining_qty = $2 WHERE id = $3",
            status,
            remaining_qty,
            order_id,
        )


async def get_open_orders_for_symbol(symbol: str) -> list[dict]:
    async with _pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM orders WHERE symbol = $1 AND status IN ('open', 'partial') ORDER BY created_at ASC",
            symbol,
        )
        return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Trades
# ---------------------------------------------------------------------------

async def insert_trade(trade_data: dict) -> dict:
    async with _pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO trades (id, symbol, price, quantity, buyer_id, seller_id, timestamp)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING *
            """,
            trade_data["id"],
            trade_data["symbol"],
            trade_data["price"],
            trade_data["quantity"],
            trade_data.get("buyer_id"),
            trade_data.get("seller_id"),
            _naive_utc(trade_data["timestamp"]),
        )
        return dict(row)


async def get_trades_for_symbol(symbol: str, limit: int = 50) -> list[dict]:
    async with _pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM trades WHERE symbol = $1 ORDER BY timestamp DESC LIMIT $2",
            symbol,
            limit,
        )
        return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

async def get_user_by_email(email: str) -> dict | None:
    async with _pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM users WHERE email = $1", email)
        return dict(row) if row else None


async def get_user_by_id(user_id: str) -> dict | None:
    async with _pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
        return dict(row) if row else None


async def create_user(email: str, hashed_password: str) -> dict:
    async with _pool.acquire() as conn:
        row = await conn.fetchrow(
            "INSERT INTO users (email, hashed_password) VALUES ($1, $2) RETURNING *",
            email,
            hashed_password,
        )
        return dict(row)
