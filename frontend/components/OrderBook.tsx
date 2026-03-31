"use client";

import { useMarketDepth } from "@/lib/ws";

export default function OrderBook({ symbol }: { symbol: string }) {
  const depth = useMarketDepth(symbol);

  const asks = [...depth.asks].reverse().slice(0, 10);
  const bids = depth.bids.slice(0, 10);

  return (
    <div className="bg-gray-900 rounded-lg p-4 w-full">
      <h2 className="text-white font-semibold text-sm mb-3">Order Book · {symbol}</h2>

      <div className="flex justify-between text-xs text-gray-500 mb-1 px-1">
        <span>Price</span>
        <span>Quantity</span>
      </div>

      {/* Asks — red, lowest ask at bottom */}
      <div className="mb-1">
        {asks.length === 0 ? (
          <div className="text-gray-600 text-xs text-center py-2">No asks</div>
        ) : (
          asks.map(([price, qty], i) => (
            <div key={i} className="flex justify-between text-xs py-0.5 px-1 hover:bg-gray-800">
              <span className="text-red-400 font-mono">{parseFloat(price).toLocaleString()}</span>
              <span className="text-gray-300 font-mono">{parseFloat(qty).toFixed(4)}</span>
            </div>
          ))
        )}
      </div>

      {/* Spread */}
      <div className="border-t border-b border-gray-700 py-1 px-1 text-xs text-gray-400 text-center my-1">
        {depth.bids[0] && depth.asks[0]
          ? `Spread: ${(parseFloat(depth.asks[0][0]) - parseFloat(depth.bids[0][0])).toFixed(2)}`
          : "—"}
      </div>

      {/* Bids — green */}
      <div className="mt-1">
        {bids.length === 0 ? (
          <div className="text-gray-600 text-xs text-center py-2">No bids</div>
        ) : (
          bids.map(([price, qty], i) => (
            <div key={i} className="flex justify-between text-xs py-0.5 px-1 hover:bg-gray-800">
              <span className="text-green-400 font-mono">{parseFloat(price).toLocaleString()}</span>
              <span className="text-gray-300 font-mono">{parseFloat(qty).toFixed(4)}</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
