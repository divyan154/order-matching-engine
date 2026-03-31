"use client";

import { useState } from "react";
import { submitOrder } from "@/lib/api";
import { getToken } from "@/lib/auth";

interface Props {
  symbol: string;
  onAuthRequired: () => void;
  onOrderPlaced: () => void;
}

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
      setMessage({ text: `Order placed. ${filled} trade(s) executed.`, ok: true });
      setQuantity("");
      setPrice("");
      onOrderPlaced();
    } catch (err: unknown) {
      setMessage({ text: err instanceof Error ? err.message : "Order failed", ok: false });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="bg-gray-900 rounded-lg p-4 w-full">
      <h2 className="text-white font-semibold text-sm mb-3">Place Order · {symbol}</h2>

      {/* Buy / Sell tabs */}
      <div className="flex mb-4 rounded overflow-hidden border border-gray-700">
        <button
          onClick={() => setSide("buy")}
          className={`flex-1 py-2 text-sm font-medium ${side === "buy" ? "bg-green-600 text-white" : "text-gray-400 hover:bg-gray-800"}`}
        >
          Buy
        </button>
        <button
          onClick={() => setSide("sell")}
          className={`flex-1 py-2 text-sm font-medium ${side === "sell" ? "bg-red-600 text-white" : "text-gray-400 hover:bg-gray-800"}`}
        >
          Sell
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-3">
        {/* Order type */}
        <select
          value={type}
          onChange={(e) => setType(e.target.value)}
          className="w-full bg-gray-800 text-white px-3 py-2 rounded text-sm border border-gray-700 focus:outline-none focus:border-blue-500"
        >
          <option value="limit">Limit</option>
          <option value="market">Market</option>
          <option value="ioc">IOC</option>
          <option value="fok">FOK</option>
        </select>

        {/* Price — hidden for market */}
        {type !== "market" && (
          <input
            type="number"
            placeholder="Price"
            value={price}
            onChange={(e) => setPrice(e.target.value)}
            required
            min="0"
            step="any"
            className="w-full bg-gray-800 text-white px-3 py-2 rounded text-sm border border-gray-700 focus:outline-none focus:border-blue-500"
          />
        )}

        <input
          type="number"
          placeholder="Quantity"
          value={quantity}
          onChange={(e) => setQuantity(e.target.value)}
          required
          min="0"
          step="any"
          className="w-full bg-gray-800 text-white px-3 py-2 rounded text-sm border border-gray-700 focus:outline-none focus:border-blue-500"
        />

        {message && (
          <p className={`text-xs ${message.ok ? "text-green-400" : "text-red-400"}`}>
            {message.text}
          </p>
        )}

        <button
          type="submit"
          disabled={loading}
          className={`w-full py-2 rounded text-sm font-medium text-white disabled:opacity-50 ${
            side === "buy" ? "bg-green-600 hover:bg-green-700" : "bg-red-600 hover:bg-red-700"
          }`}
        >
          {loading ? "Placing..." : `${side === "buy" ? "Buy" : "Sell"} ${symbol}`}
        </button>
      </form>
    </div>
  );
}
