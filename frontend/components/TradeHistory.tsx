"use client";

import { useTradeFeed } from "@/lib/ws";

export default function TradeHistory({ symbol }: { symbol: string }) {
  const trades = useTradeFeed(symbol);

  return (
    <div
      style={{
        background: "var(--bg-surface)",
        border: "1px solid var(--border)",
        borderRadius: "12px",
        overflow: "hidden",
      }}
      className="w-full"
    >
      <div
        style={{ borderBottom: "1px solid var(--border)" }}
        className="px-4 py-3 flex items-center justify-between"
      >
        <span className="text-xs font-semibold tracking-widest uppercase" style={{ color: "var(--text-secondary)" }}>
          Recent Trades
        </span>
        <span className="text-xs font-mono font-medium" style={{ color: "var(--text-secondary)" }}>
          {symbol}
        </span>
      </div>

      {/* Column headers */}
      <div
        className="flex justify-between text-xs px-4 py-2"
        style={{ color: "var(--text-secondary)", borderBottom: "1px solid var(--border)" }}
      >
        <span className="w-24">Price (USDT)</span>
        <span className="w-20 text-right">Amount</span>
        <span className="w-12 text-center">Side</span>
        <span className="w-20 text-right">Time</span>
      </div>

      <div className="overflow-y-auto" style={{ maxHeight: "400px" }}>
        {trades.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 gap-2">
            <div
              style={{
                width: "32px",
                height: "32px",
                borderRadius: "50%",
                border: "2px solid var(--border)",
                borderTopColor: "var(--accent)",
                animation: "spin 1s linear infinite",
              }}
            />
            <span className="text-xs" style={{ color: "var(--text-secondary)" }}>
              Waiting for trades...
            </span>
          </div>
        ) : (
          trades.map((t, idx) => (
            <div
              key={t.id}
              className={`flex justify-between items-center text-xs px-4 py-1.5 ${idx === 0 ? "trade-row-new" : ""}`}
              style={{
                borderBottom: "1px solid var(--border-subtle, #111827)",
              }}
            >
              <span
                className="w-24 font-mono font-medium"
                style={{ color: t.aggressor_side === "buy" ? "var(--green)" : "var(--red)" }}
              >
                {t.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </span>
              <span className="w-20 text-right font-mono" style={{ color: "var(--text-primary)" }}>
                {t.quantity.toFixed(4)}
              </span>
              <span className="w-12 flex justify-center">
                <span
                  style={{
                    background:
                      t.aggressor_side === "buy"
                        ? "var(--green-dim)"
                        : "var(--red-dim)",
                    color: t.aggressor_side === "buy" ? "var(--green)" : "var(--red)",
                    borderRadius: "4px",
                    padding: "1px 6px",
                    fontSize: "10px",
                    fontWeight: "600",
                    letterSpacing: "0.05em",
                  }}
                >
                  {(t.aggressor_side ?? "—").toUpperCase()}
                </span>
              </span>
              <span className="w-20 text-right font-mono" style={{ color: "var(--text-secondary)" }}>
                {new Date(t.timestamp).toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                  second: "2-digit",
                })}
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
