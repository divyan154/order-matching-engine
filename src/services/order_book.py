import asyncio
import json
from typing import List
from fastapi import WebSocket
from sortedcontainers import SortedDict
from collections import deque
from src.models.order import Order, Side, OrderType
from src.models.trade import Trade
from src.models.book_entry import OrderBookEntry
from src.utils.logger import logger
from datetime import datetime,timezone

class OrderBook:
    def __init__(self, symbol: str,market_clients: List[WebSocket] = None, trade_clients: List[WebSocket] = None):
        self.symbol = symbol
        self.bids = SortedDict(lambda x: -x)
        self.asks = SortedDict()
        self.trades = []
        self.market_clients = market_clients if market_clients else []
        self.trade_clients = trade_clients if trade_clients else []

    async def add_order(self, order: Order):
        logger.info(f"New order: {order}")

        if order.type == OrderType.MARKET:
            await self._match_market(order)
        elif order.type == OrderType.LIMIT:
            await self._match_limit(order)
      
            # Add remaining quantity to book
            if order.quantity > 0:
                self._add_to_book(order)
        elif order.type == OrderType.IOC:
          await self._match_limit(order)
          # Don't add remaining to book (cancel remainder)

        elif order.type == OrderType.FOK:
           if self._can_fully_match(order):
            await self._match_limit(order)
           else:
            logger.info(f"FOK order not filled and canceled: {order.id}")
        await self._update_bbo() 

    def _add_to_book(self, order: Order):
        book = self.bids if order.side == Side.BUY else self.asks
        if order.price not in book:
            book[order.price] = deque()
        book[order.price].append(OrderBookEntry(
            order_id=order.id,
            quantity=order.quantity,
            timestamp=order.timestamp
        ))

    async def _match_market(self, order: Order):
        book = self.asks if order.side == Side.BUY else self.bids
        while order.quantity > 0 and book:
            best_price = next(iter(book))
            queue = book[best_price]
            while queue and order.quantity > 0:
                top = queue[0]
                traded_qty = min(order.quantity, top.quantity)
                await self._record_trade(order, top, best_price, traded_qty)

                top.quantity -= traded_qty
                order.quantity -= traded_qty

                if top.quantity <= 0:
                    queue.popleft()
            if not queue:
                del book[best_price]

    async def _match_limit(self, order: Order):
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
                await self._record_trade(order, top, best_price, traded_qty)

                top.quantity -= traded_qty
                order.quantity -= traded_qty
                if top.quantity <= 0:
                    queue.popleft()
            if not queue:
                del contra_book[best_price]

    async def _record_trade(self, incoming: Order, existing: OrderBookEntry, price: float, qty: float):
        buy_id = incoming.id if incoming.side == Side.BUY else existing.order_id
        sell_id = incoming.id if incoming.side == Side.SELL else existing.order_id
        maker_id = existing.order_id
        taker_id = incoming.id
        aggressor_side = incoming.side.value  # "buy" or "sell"

        trade = Trade(
            symbol=self.symbol,
            price=price,
            quantity=qty,
            buy_order_id=buy_id,
            sell_order_id=sell_id,
            maker_id=maker_id,
            taker_id=taker_id,
            aggressor_side=aggressor_side
        )

        self.trades.append(trade)
        logger.info(f"Trade executed: {trade}")
        await self.broadcast_trade(trade)

    def get_order_book_depth(self, depth=10):
        def format_side(side):
            result = []
            for price, queue in list(side.items())[:depth]:
                total_qty = sum(entry.quantity for entry in queue)
                result.append([str(price), str(total_qty)])
            return result

        return {
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            "symbol": self.symbol,  # Or use dynamic symbol if multi-asset
            "asks": format_side(self.asks),
            "bids": format_side(self.bids)
        }
    def get_bbo(self):
        best_bid = next(iter(self.bids), None)
        best_ask = next(iter(self.asks), None)
        return {"bid": best_bid, "ask": best_ask}

    async def _update_bbo(self):
         depth_snapshot = self.get_order_book_depth()
         await self.broadcast_market_depth(depth_snapshot)
    
    async def broadcast_market_depth(self, depth_snapshot):
    
        message = json.dumps({
            "type": "market_depth",
            "data": depth_snapshot
        })
        for ws in self.market_clients:
            try:
                await ws.send_text(message)
                logger.info(f"Broadcasted market depth: {message}")
            except:
                self.market_clients.remove(ws)

   
    async def broadcast_trade(self, trade: Trade):
       

        message = json.dumps({
                "type": "trade",
                "data": {
                    "price": trade.price,
                    "quantity": trade.quantity,
                    "symbol": trade.symbol,  # Or use dynamic symbol if multi-asset
                    "timestamp": trade.timestamp.isoformat() + "Z",
                 
                    "aggressor_side": trade.aggressor_side,
                    "maker_order_id": trade.maker_id, # id of resting order
                    "taker_order_id":trade.taker_id  # id of incoming order
                }
             }, default=str)

        for ws in self.trade_clients:
            try:
                await ws.send_text(message)
                logger.info(f"Broadcasted trade: {message}")

            except:
                self.trade_clients.remove(ws)
    def _can_fully_match(self, order: Order) -> bool:
        book = self.asks if order.side == Side.BUY else self.bids
        total = 0.0

        for price, queue in book.items():
            if (order.side == Side.BUY and price > order.price) or \
            (order.side == Side.SELL and price < order.price):
                break
            for entry in queue:
                total += entry.quantity
                if total >= order.quantity:
                    return True
        return False
