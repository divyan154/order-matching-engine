"use client";

import { useState } from "react";
import Header from "@/components/Header";
import OrderBook from "@/components/OrderBook";
import TradingPanel from "@/components/TradingPanel";
import TradeHistory from "@/components/TradeHistory";
import AuthModal from "@/components/AuthModal";

const SYMBOLS = [
  { id: "BTCUSDT", label: "BTC/USDT" },
  { id: "ETHUSDT", label: "ETH/USDT" },
  { id: "BNBUSDT", label: "BNB/USDT" },
];

export default function Home() {
  const [symbol, setSymbol] = useState("BTCUSDT");
  const [showAuth, setShowAuth] = useState(false);

  return (
    <div
      style={{ background: "var(--bg-base)", minHeight: "100vh" }}
      className="text-white"
    >
      <Header onAuthRequired={() => setShowAuth(true)} />

      {/* Symbol selector */}
      <div
        style={{
          background: "var(--bg-surface)",
          borderBottom: "1px solid var(--border)",
        }}
        className="flex gap-1 px-6 py-2"
      >
        {SYMBOLS.map((s) => (
          <button
            key={s.id}
            onClick={() => setSymbol(s.id)}
            style={
              symbol === s.id
                ? {
                    background: "var(--accent-glow)",
                    color: "#93c5fd",
                    borderBottom: "2px solid var(--accent)",
                    borderTop: "none",
                    borderLeft: "none",
                    borderRight: "none",
                    borderRadius: "0",
                  }
                : {
                    color: "var(--text-secondary)",
                    background: "transparent",
                    border: "none",
                    borderBottom: "2px solid transparent",
                    borderRadius: "0",
                  }
            }
            className="px-4 py-2 text-sm font-medium tracking-wide transition-all duration-150 hover:text-white"
          >
            {s.label}
          </button>
        ))}
      </div>

      {/* Main layout */}
      <main className="grid grid-cols-12 gap-3 p-4">
        <div className="col-span-3">
          <OrderBook symbol={symbol} />
        </div>
        <div className="col-span-5">
          <TradeHistory symbol={symbol} />
        </div>
        <div className="col-span-4">
          <TradingPanel
            symbol={symbol}
            onAuthRequired={() => setShowAuth(true)}
            onOrderPlaced={() => {}}
          />
        </div>
      </main>

      {showAuth && (
        <AuthModal
          onSuccess={() => {
            setShowAuth(false);
            window.location.reload();
          }}
          onClose={() => setShowAuth(false)}
        />
      )}
    </div>
  );
}
