from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.models.order import Order, OrderCreate
from src.services import auth_service, db, matching_engine

router = APIRouter(prefix="/orders", tags=["orders"])

# Optional auth — orders work anonymously too (user_id stays None)
optional_bearer = HTTPBearer(auto_error=False)


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(optional_bearer),
) -> dict | None:
    if not credentials:
        return None
    try:
        user_id = auth_service.decode_token(credentials.credentials)
        return await db.get_user_by_id(user_id)
    except Exception:
        return None


@router.post("", status_code=201)
async def create_order(
    body: OrderCreate,
    current_user: dict | None = Depends(get_optional_user),
):
    user_id = str(current_user["id"]) if current_user else None

    order = Order(
        symbol=body.symbol,
        side=body.side,
        type=body.type,
        price=body.price,
        quantity=body.quantity,
        user_id=user_id,
    )

    await db.insert_order({
        "id": order.id,
        "user_id": order.user_id,
        "symbol": order.symbol,
        "side": order.side.value,
        "type": order.type.value,
        "price": order.price,
        "quantity": order.quantity,
        "remaining_qty": order.remaining_qty,
        "status": order.status.value,
        "timestamp": order.timestamp,
    })

    trades = await matching_engine.submit_order(order)

    return {
        "order_id": order.id,
        "status": order.status.value,
        "symbol": order.symbol,
        "side": order.side.value,
        "type": order.type.value,
        "price": order.price,
        "quantity": order.quantity,
        "remaining_qty": order.remaining_qty,
        "trades_executed": len(trades),
        "trades": [
            {
                "id": t.id,
                "price": t.price,
                "quantity": t.quantity,
                "aggressor_side": t.aggressor_side,
            }
            for t in trades
        ],
    }


@router.get("/{order_id}")
async def get_order(order_id: str):
    order = await db.get_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.delete("/{order_id}")
async def cancel_order(order_id: str):
    order = await db.get_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order["status"] not in ("open", "partial"):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel order with status '{order['status']}'"
        )

    book = matching_engine.get_book(order["symbol"])
    removed_from_book = book.cancel_order(order_id) if book else False

    await db.update_order(order_id, "cancelled", float(order["remaining_qty"]))

    return {"cancelled": True, "order_id": order_id, "removed_from_book": removed_from_book}
