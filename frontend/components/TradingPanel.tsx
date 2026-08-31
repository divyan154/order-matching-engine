"use client";

import { useState } from "react";
import { submitOrder } from "@/lib/api";
import { getToken } from "@/lib/auth";

interface Props {
  symbol: string;
  onAuthRequired: () => void;
  onOrderPlaced: () => void;
}

const ORDER_TYPES = [
  { value: "limit", label: "Limit" },
  { value: "market", label: "Market" },
  { value: "ioc", label: "IOC" },
  { value: "fok", label: "FOK" },
];

export default function TradingPanel({ symbol, onAuthRequired, onOrderPlaced }: Props) {
  const [side, setSide] = useState<"buy" | "sell">("buy");
  const [type, setType] = useState("limit");
  const [price, setPrice] = useState("");
  const [quantity, setQuantity] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ text: string; ok: boolean } | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setMessage(null);

    if (!getToken()) {
      onAuthRequired();
      return;
    }

    setLoading(true);
    try {
      const result = await submitOrder({
        symbol,
        side,
        type,
        price: type === "market" ? 0 : parseFloat(price),
        quantity: parseFloat(quantity),
      });
      const filled = result.trades_executed;
      setMessage({ text: `Order placed · ${filled} trade(s) executed`, ok: true });
      setQuantity("");
      setPrice("");
      onOrderPlaced();
    } catch (err: unknown) {
      setMessage({ text: err instanceof Error ? err.message : "Order failed", ok: false });
    } finally {
      setLoading(false);
    }
  }

  const isBuy = side === "buy";

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
          Place Order
        </span>
        <span className="text-xs font-mono font-medium" style={{ color: "var(--text-secondary)" }}>
          {symbol}
        </span>
      </div>

      <div className="p-4">
        {/* Buy / Sell tabs */}
        <div
          style={{ background: "var(--bg-base)", borderRadius: "8px", padding: "3px" }}
          className="flex mb-4"
        >
          <button
            onClick={() => setSide("buy")}
            style={
              isBuy
                ? {
                    background: "linear-gradient(135deg, #16a34a, #22c55e)",
                    color: "white",
                    boxShadow: "0 2px 8px rgba(34,197,94,0.3)",
                    borderRadius: "6px",
                  }
                : {
                    color: "var(--text-secondary)",
                    background: "transparent",
                    borderRadius: "6px",
                  }
            }
            className="flex-1 py-2 text-sm font-semibold transition-all duration-150"
          >
            Buy
          </button>
          <button
            onClick={() => setSide("sell")}
            style={
              !isBuy
                ? {
                    background: "linear-gradient(135deg, #dc2626, #ef4444)",
                    color: "white",
                    boxShadow: "0 2px 8px rgba(239,68,68,0.3)",
                    borderRadius: "6px",
                  }
                : {
                    color: "var(--text-secondary)",
                    background: "transparent",
                    borderRadius: "6px",
                  }
            }
            className="flex-1 py-2 text-sm font-semibold transition-all duration-150"
          >
            Sell
          </button>
        </div>

        {/* Order type pills */}
        <div className="flex gap-1.5 mb-4">
          {ORDER_TYPES.map((ot) => (
            <button
              key={ot.value}
              onClick={() => setType(ot.value)}
              style={
                type === ot.value
                  ? {
                      background: "var(--accent-glow)",
                      color: "#93c5fd",
                      border: "1px solid rgba(59,130,246,0.4)",
                      borderRadius: "6px",
                    }
                  : {
                      background: "var(--bg-base)",
                      color: "var(--text-secondary)",
                      border: "1px solid var(--border)",
                      borderRadius: "6px",
                    }
              }
              className="flex-1 py-2 text-xs font-medium transition-all duration-150"
            >
              {ot.label}
            </button>
          ))}
        </div>

        <form onSubmit={handleSubmit} className="space-y-3">
          {type !== "market" && (
            <div>
              <label className="block text-xs mb-1.5" style={{ color: "var(--text-secondary)" }}>
                Price (USDT)
              </label>
              <input
                type="number"
                placeholder="0.00"
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                required
                min="0"
                step="any"
                style={{
                  background: "var(--bg-base)",
                  border: "1px solid var(--border)",
                  color: "var(--text-primary)",
                  borderRadius: "8px",
                  outline: "none",
                  width: "100%",
                  padding: "10px 12px",
                  fontSize: "13px",
                  fontFamily: "var(--font-mono)",
                  transition: "border-color 0.15s",
                }}
                onFocus={(e) => (e.target.style.borderColor = "var(--accent)")}
                onBlur={(e) => (e.target.style.borderColor = "var(--border)")}
              />
            </div>
          )}

          <div>
            <label className="block text-xs mb-1.5" style={{ color: "var(--text-secondary)" }}>
              Amount ({symbol.replace("USDT", "")})
            </label>
            <input
              type="number"
              placeholder="0.0000"
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
              required
              min="0"
              step="any"
              style={{
                background: "var(--bg-base)",
                border: "1px solid var(--border)",
                color: "var(--text-primary)",
                borderRadius: "8px",
                outline: "none",
                width: "100%",
                padding: "10px 12px",
                fontSize: "13px",
                fontFamily: "var(--font-mono)",
                transition: "border-color 0.15s",
              }}
              onFocus={(e) => (e.target.style.borderColor = "var(--accent)")}
              onBlur={(e) => (e.target.style.borderColor = "var(--border)")}
            />
          </div>

          {message && (
            <div
              style={{
                background: message.ok ? "rgba(34,197,94,0.08)" : "rgba(239,68,68,0.08)",
                border: `1px solid ${message.ok ? "rgba(34,197,94,0.25)" : "rgba(239,68,68,0.25)"}`,
                borderRadius: "6px",
                padding: "8px 10px",
                color: message.ok ? "var(--green)" : "var(--red)",
              }}
              className="text-xs"
            >
              {message.text}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            style={
              isBuy
                ? {
                    background: loading
                      ? "rgba(34,197,94,0.3)"
                      : "linear-gradient(135deg, #16a34a, #22c55e)",
                    boxShadow: loading ? "none" : "0 4px 14px rgba(34,197,94,0.25)",
                    borderRadius: "8px",
                    color: "white",
                    width: "100%",
                    padding: "11px",
                    fontSize: "14px",
                    fontWeight: "600",
                    border: "none",
                    cursor: loading ? "not-allowed" : "pointer",
                    transition: "all 0.15s",
                  }
                : {
                    background: loading
                      ? "rgba(239,68,68,0.3)"
                      : "linear-gradient(135deg, #dc2626, #ef4444)",
                    boxShadow: loading ? "none" : "0 4px 14px rgba(239,68,68,0.25)",
                    borderRadius: "8px",
                    color: "white",
                    width: "100%",
                    padding: "11px",
                    fontSize: "14px",
                    fontWeight: "600",
                    border: "none",
                    cursor: loading ? "not-allowed" : "pointer",
                    transition: "all 0.15s",
                  }
            }
          >
            {loading ? "Placing..." : `${isBuy ? "Buy" : "Sell"} ${symbol.replace("USDT", "")}`}
          </button>
        </form>
      </div>
    </div>
  );
}
