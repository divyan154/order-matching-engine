"use client";

import { useTradeFeed } from "@/lib/ws";

export default function TradeHistory({ symbol }: { symbol: string }) {
  const trades = useTradeFeed(symbol);

  return (
    <div className="bg-gray-900 rounded-lg p-4 w-full">
      <h2 className="text-white font-semibold text-sm mb-3">Recent Trades · {symbol}</h2>

      <div className="flex justify-between text-xs text-gray-500 mb-1 px-1">
        <span>Price</span>
        <span>Qty</span>
        <span>Side</span>
        <span>Time</span>
      </div>

      <div className="space-y-0.5 max-h-80 overflow-y-auto">
        {trades.length === 0 ? (
          <div className="text-gray-600 text-xs text-center py-4">Waiting for trades...</div>
        ) : (
          trades.map((t) => (
            <div key={t.id} className="flex justify-between text-xs py-0.5 px-1 hover:bg-gray-800">
              <span className={`font-mono ${t.aggressor_side === "buy" ? "text-green-400" : "text-red-400"}`}>
                {t.price.toLocaleString()}
              </span>
              <span className="text-gray-300 font-mono">{t.quantity.toFixed(4)}</span>
              <span className={t.aggressor_side === "buy" ? "text-green-400" : "text-red-400"}>
                {t.aggressor_side.toUpperCase()}
              </span>
              <span className="text-gray-500">
                {new Date(t.timestamp).toLocaleTimeString()}
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
