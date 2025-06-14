from sortedcontainers import SortedDict
from collections import deque
from src.models.order import Order, Side, OrderType
from src.models.trade import Trade
from src.models.book_entry import OrderBookEntry
from src.utils.logger import logger


class OrderBook:
    def __init__(self):
        self.bids = SortedDict(lambda x: -x)  # Highest price first
        self.asks = SortedDict()              # Lowest price first
        self.trades = []

    def add_order(self, order: Order):
        logger.info(f"New order: {order}")

        if order.type == OrderType.MARKET:
            self._match_market(order)
        elif order.type == OrderType.LIMIT:
            self._match_limit(order)

            # Add remaining quantity to book
            if order.quantity > 0:
                self._add_to_book(order)

        self._update_bbo()

    def _add_to_book(self, order: Order):
        book = self.bids if order.side == Side.BUY else self.asks
        if order.price not in book:
            book[order.price] = deque()
        book[order.price].append(OrderBookEntry(
            order_id=order.id,
            quantity=order.quantity,
            timestamp=order.timestamp
        ))

    def _match_market(self, order: Order):
        book = self.asks if order.side == Side.BUY else self.bids
        while order.quantity > 0 and book:
            best_price = next(iter(book))
            queue = book[best_price]
            while queue and order.quantity > 0:
                top = queue[0]
                traded_qty = min(order.quantity, top.quantity)
                self._record_trade(order, top, best_price, traded_qty)

                top.quantity -= traded_qty
                order.quantity -= traded_qty

                if top.quantity <= 0:
                    queue.popleft()
            if not queue:
                del book[best_price]

    def _match_limit(self, order: Order):
        contra_book = self.asks if order.side == Side.BUY else self.bids

        def is_cross(price):
            return (order.side == Side.BUY and price <= order.price) or \
                   (order.side == Side.SELL and price >= order.price)

        while order.quantity > 0 and contra_book:
            best_price = next(iter(contra_book))
            if not is_cross(best_price):
                break
            queue = contra_book[best_price]
            while queue and order.quantity > 0:
                top = queue[0]
                traded_qty = min(order.quantity, top.quantity)
                self._record_trade(order, top, best_price, traded_qty)

                top.quantity -= traded_qty
                order.quantity -= traded_qty
                if top.quantity <= 0:
                    queue.popleft()
            if not queue:
                del contra_book[best_price]

    def _record_trade(self, incoming: Order, existing: OrderBookEntry, price: float, qty: float):
        buy_id = incoming.id if incoming.side == Side.BUY else existing.order_id
        sell_id = incoming.id if incoming.side == Side.SELL else existing.order_id
        trade = Trade(
            price=price,
            quantity=qty,
            buy_order_id=buy_id,
            sell_order_id=sell_id
        )
        self.trades.append(trade)
        logger.info(f"Trade executed: {trade}")

    def get_bbo(self):
        best_bid = next(iter(self.bids), None)
        best_ask = next(iter(self.asks), None)
        return {"bid": best_bid, "ask": best_ask}

    def _update_bbo(self):
        bbo = self.get_bbo()
        logger.info(f"BBO updated: {bbo}")
