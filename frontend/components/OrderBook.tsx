"use client";

import { useMarketDepth } from "@/lib/ws";

export default function OrderBook({ symbol }: { symbol: string }) {
  const depth = useMarketDepth(symbol);

  const asks = [...depth.asks].reverse().slice(0, 12);
  const bids = depth.bids.slice(0, 12);

  const allQtys = [
    ...asks.map(([, q]) => parseFloat(q)),
    ...bids.map(([, q]) => parseFloat(q)),
  ];
  const maxQty = allQtys.length > 0 ? Math.max(...allQtys) : 1;

  const spread =
    depth.bids[0] && depth.asks[0]
      ? (parseFloat(depth.asks[0][0]) - parseFloat(depth.bids[0][0])).toFixed(2)
      : null;

  return (
    <div
      style={{
        background: "var(--bg-surface)",
        border: "1px solid var(--border)",
        borderRadius: "12px",
      }}
      className="w-full overflow-hidden"
    >
      <div
        style={{ borderBottom: "1px solid var(--border)" }}
        className="px-4 py-3 flex items-center justify-between"
      >
        <span className="text-xs font-semibold tracking-widest uppercase" style={{ color: "var(--text-secondary)" }}>
          Order Book
        </span>
        <span className="text-xs font-mono font-medium" style={{ color: "var(--text-secondary)" }}>
          {symbol}
        </span>
      </div>

      <div className="px-3 py-1">
        {/* Column headers */}
        <div className="flex justify-between text-xs px-1 py-1.5" style={{ color: "var(--text-secondary)" }}>
          <span>Price (USDT)</span>
          <span>Amount</span>
        </div>

        {/* Asks */}
        <div className="mb-0.5">
          {asks.length === 0 ? (
            <div className="text-center py-4 text-xs" style={{ color: "var(--text-muted)" }}>
              No asks
            </div>
          ) : (
            asks.map(([price, qty], i) => {
              const pct = (parseFloat(qty) / maxQty) * 100;
              return (
                <div
                  key={i}
                  className="relative flex justify-between text-xs py-0.5 px-1 rounded"
                  style={{ overflow: "hidden" }}
                >
                  <div
                    className="absolute inset-y-0 right-0"
                    style={{
                      width: `${pct}%`,
                      background: "var(--red-dim)",
                    }}
                  />
                  <span className="relative font-mono" style={{ color: "var(--red)" }}>
                    {parseFloat(price).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </span>
                  <span className="relative font-mono" style={{ color: "var(--text-primary)" }}>
                    {parseFloat(qty).toFixed(4)}
                  </span>
                </div>
              );
            })
          )}
        </div>

        {/* Spread */}
        <div
          style={{ borderTop: "1px solid var(--border)", borderBottom: "1px solid var(--border)" }}
          className="py-1.5 px-1 my-0.5 flex items-center justify-center gap-2"
        >
          {spread !== null ? (
            <>
              <span className="text-xs font-mono font-semibold" style={{ color: "var(--accent)" }}>
                {spread}
              </span>
              <span className="text-xs" style={{ color: "var(--text-secondary)" }}>
                spread
              </span>
            </>
          ) : (
            <span className="text-xs" style={{ color: "var(--text-muted)" }}>—</span>
          )}
        </div>

        {/* Bids */}
        <div className="mt-0.5">
          {bids.length === 0 ? (
            <div className="text-center py-4 text-xs" style={{ color: "var(--text-muted)" }}>
              No bids
            </div>
          ) : (
            bids.map(([price, qty], i) => {
              const pct = (parseFloat(qty) / maxQty) * 100;
              return (
                <div
                  key={i}
                  className="relative flex justify-between text-xs py-0.5 px-1 rounded"
                  style={{ overflow: "hidden" }}
                >
                  <div
                    className="absolute inset-y-0 right-0"
                    style={{
                      width: `${pct}%`,
                      background: "var(--green-dim)",
                    }}
                  />
                  <span className="relative font-mono" style={{ color: "var(--green)" }}>
                    {parseFloat(price).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </span>
                  <span className="relative font-mono" style={{ color: "var(--text-primary)" }}>
                    {parseFloat(qty).toFixed(4)}
                  </span>
                </div>
              );
            })
          )}
        </div>
      </div>

      <div className="pb-2" />
    </div>
  );
}
