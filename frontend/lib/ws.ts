import { useEffect, useState, useRef } from "react";

const WS_BASE =
  typeof window !== "undefined"
    ? `ws://${window.location.hostname}:8000`
    : "ws://localhost:8000";

export interface DepthData {
  symbol: string;
  bids: [string, string][];
  asks: [string, string][];
  timestamp: string;
}

export interface TradeData {
  id: string;
  price: number;
  quantity: number;
  symbol: string;
  timestamp: string;
  aggressor_side: string;
  maker_order_id: string;
  taker_order_id: string;
}

export function useMarketDepth(symbol: string) {
  const [depth, setDepth] = useState<DepthData>({ symbol, bids: [], asks: [], timestamp: "" });
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const ws = new WebSocket(`${WS_BASE}/ws/market/${symbol}`);
    wsRef.current = ws;

    ws.onmessage = (e) => {
      const msg = JSON.parse(e.data);
      if (msg.type === "market_depth") setDepth(msg.data);
    };
    ws.onerror = () => {};

    return () => ws.close();
  }, [symbol]);

  return depth;
}

export function useTradeFeed(symbol: string) {
  const [trades, setTrades] = useState<TradeData[]>([]);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const ws = new WebSocket(`${WS_BASE}/ws/trades/${symbol}`);
    wsRef.current = ws;

    ws.onmessage = (e) => {
      const msg = JSON.parse(e.data);
      if (msg.type === "trade") {
        setTrades((prev) => [msg.data, ...prev].slice(0, 30));
      }
    };
    ws.onerror = () => {};

    return () => ws.close();
  }, [symbol]);

  return trades;
}
