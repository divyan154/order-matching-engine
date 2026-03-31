"""
In-memory order book. Fully synchronous — no I/O.
All DB writes and WebSocket broadcasts happen in the matching_engine worker.
"""

from collections import deque
from datetime import datetime, timezone
from typing import List

from sortedcontainers import SortedDict

from src.models.book_entry import OrderBookEntry
from src.models.order import Order, OrderStatus, Side, OrderType
from src.models.trade import Trade
from src.utils.logger import logger


class OrderBook:
    def __init__(self, symbol: str):
        self.symbol = symbol
        # bids: highest price first
        self.bids: SortedDict = SortedDict(lambda x: -x)
        # asks: lowest price first
        self.asks: SortedDict = SortedDict()

        # order_id → (price, side) for O(1) cancel lookup
        self._order_index: dict[str, tuple[float, Side]] = {}

        # WebSocket clients (managed by main.py)
        self.market_clients: list = []
        self.trade_clients: list = []

    # ------------------------------------------------------------------
    # Public interface called by matching_engine worker
    # ------------------------------------------------------------------

    def match(self, order: Order) -> list[Trade]:
        """
        Match incoming order against the book.
        Mutates the book in-place.
        Returns list of Trade objects (no I/O).
        """
        logger.info(f"[OrderBook:{self.symbol}] matching {order.type} {order.side} qty={order.quantity} price={order.price}")

        if order.type == OrderType.MARKET:
            trades = self._match_market(order)
        elif order.type == OrderType.LIMIT:
            trades = self._match_limit(order)
            if order.remaining_qty > 0:
                self._add_to_book(order)
        elif order.type == OrderType.IOC:
            trades = self._match_limit(order)
            # remainder cancelled — don't add to book
        elif order.type == OrderType.FOK:
            if self._can_fully_match(order):
                trades = self._match_limit(order)
            else:
                logger.info(f"[OrderBook:{self.symbol}] FOK cancelled: {order.id}")
                order.status = OrderStatus.CANCELLED
                trades = []
        else:
            trades = []

        return trades

    def cancel_order(self, order_id: str) -> bool:
        """Remove a resting order from the book. Returns True if found."""
        if order_id not in self._order_index:
            return False

        price, side = self._order_index.pop(order_id)
        book = self.bids if side == Side.BUY else self.asks

        if price in book:
            book[price] = deque(
                e for e in book[price] if e.order_id != order_id
            )
            if not book[price]:
                del book[price]

        logger.info(f"[OrderBook:{self.symbol}] cancelled order {order_id}")
        return True

    def restore_order(self, order: Order):
        """Add an order directly to the book without matching (for recovery on startup)."""
        self._add_to_book(order)

    # ------------------------------------------------------------------
    # Matching internals
    # ------------------------------------------------------------------

    def _match_market(self, order: Order) -> list[Trade]:
        contra = self.asks if order.side == Side.BUY else self.bids
        trades = []

        while order.remaining_qty > 0 and contra:
            best_price = next(iter(contra))
            queue = contra[best_price]

            while queue and order.remaining_qty > 0:
                top = queue[0]
                traded_qty = min(order.remaining_qty, top.quantity)
                trade = self._make_trade(order, top, best_price, traded_qty)
                trades.append(trade)

                top.quantity -= traded_qty
                order.remaining_qty -= traded_qty

                if top.quantity <= 0:
                    queue.popleft()
                    self._order_index.pop(top.order_id, None)

            if not queue:
                del contra[best_price]

        return trades

    def _match_limit(self, order: Order) -> list[Trade]:
        contra = self.asks if order.side == Side.BUY else self.bids
        trades = []

        def crosses(price: float) -> bool:
            if order.side == Side.BUY:
                return price <= order.price
            return price >= order.price

        while order.remaining_qty > 0 and contra:
            best_price = next(iter(contra))
            if not crosses(best_price):
                break

            queue = contra[best_price]
            while queue and order.remaining_qty > 0:
                top = queue[0]
                traded_qty = min(order.remaining_qty, top.quantity)
                trade = self._make_trade(order, top, best_price, traded_qty)
                trades.append(trade)

                top.quantity -= traded_qty
                order.remaining_qty -= traded_qty

                if top.quantity <= 0:
                    queue.popleft()
                    self._order_index.pop(top.order_id, None)

            if not queue:
                del contra[best_price]

        return trades

    def _make_trade(self, incoming: Order, resting: OrderBookEntry, price: float, qty: float) -> Trade:
        buyer_id = incoming.user_id if incoming.side == Side.BUY else resting.user_id
        seller_id = resting.user_id if incoming.side == Side.BUY else incoming.user_id

        trade = Trade(
            symbol=self.symbol,
            price=price,
            quantity=qty,
            buyer_id=buyer_id,
            seller_id=seller_id,
            maker_order_id=resting.order_id,
            taker_order_id=incoming.id,
            aggressor_side=incoming.side.value,
        )
        logger.info(f"[OrderBook:{self.symbol}] trade: price={price} qty={qty} aggressor={incoming.side.value}")
        return trade

    def _add_to_book(self, order: Order):
        book = self.bids if order.side == Side.BUY else self.asks
        if order.price not in book:
            book[order.price] = deque()
        entry = OrderBookEntry(
            order_id=order.id,
            quantity=order.remaining_qty,
            timestamp=order.timestamp,
            user_id=order.user_id,
        )
        book[order.price].append(entry)
        self._order_index[order.id] = (order.price, order.side)

    def _can_fully_match(self, order: Order) -> bool:
        contra = self.asks if order.side == Side.BUY else self.bids
        total = 0.0
        for price, queue in contra.items():
            if order.side == Side.BUY and price > order.price:
                break
            if order.side == Side.SELL and price < order.price:
                break
            for entry in queue:
                total += entry.quantity
                if total >= order.remaining_qty:
                    return True
        return False

    # ------------------------------------------------------------------
    # Read-only queries
    # ------------------------------------------------------------------

    def get_order_book_depth(self, depth: int = 10) -> dict:
        def format_side(side_dict):
            result = []
            for price, queue in list(side_dict.items())[:depth]:
                total_qty = sum(e.quantity for e in queue)
                result.append([str(price), str(total_qty)])
            return result

        return {
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            "symbol": self.symbol,
            "bids": format_side(self.bids),
            "asks": format_side(self.asks),
        }

    def get_bbo(self) -> dict:
        best_bid = next(iter(self.bids), None)
        best_ask = next(iter(self.asks), None)
        return {"bid": best_bid, "ask": best_ask}
