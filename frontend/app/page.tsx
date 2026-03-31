"use client";

import { useState } from "react";
import Header from "@/components/Header";
import OrderBook from "@/components/OrderBook";
import TradingPanel from "@/components/TradingPanel";
import TradeHistory from "@/components/TradeHistory";
import AuthModal from "@/components/AuthModal";

const SYMBOLS = ["BTCUSDT", "ETHUSDT", "BNBUSDT"];

export default function Home() {
  const [symbol, setSymbol] = useState("BTCUSDT");
  const [showAuth, setShowAuth] = useState(false);
  const [orderKey, setOrderKey] = useState(0);

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <Header onAuthRequired={() => setShowAuth(true)} />

      {/* Symbol tabs */}
      <div className="flex gap-1 px-6 pt-4">
        {SYMBOLS.map((s) => (
          <button
            key={s}
            onClick={() => setSymbol(s)}
            className={`px-4 py-1.5 rounded text-sm font-medium ${
              symbol === s
                ? "bg-blue-600 text-white"
                : "bg-gray-800 text-gray-400 hover:bg-gray-700"
            }`}
          >
            {s}
          </button>
        ))}
      </div>

      {/* Main layout */}
      <main className="grid grid-cols-12 gap-4 p-6">
        <div className="col-span-3">
          <OrderBook symbol={symbol} />
        </div>
        <div className="col-span-5">
          <TradeHistory key={orderKey} symbol={symbol} />
        </div>
        <div className="col-span-4">
          <TradingPanel
            symbol={symbol}
            onAuthRequired={() => setShowAuth(true)}
            onOrderPlaced={() => setOrderKey((k) => k + 1)}
          />
        </div>
      </main>

      {showAuth && (
        <AuthModal
          onSuccess={() => { setShowAuth(false); window.location.reload(); }}
          onClose={() => setShowAuth(false)}
        />
      )}
    </div>
  );
}
