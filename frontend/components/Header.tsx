"use client";

import { useState, useEffect } from "react";
import { getUser, clearAuth } from "@/lib/auth";

interface Props {
  onAuthRequired: () => void;
}

export default function Header({ onAuthRequired }: Props) {
  const [user, setUser] = useState<{ email: string } | null>(null);

  useEffect(() => {
    setUser(getUser());
  }, []);

  function handleLogout() {
    clearAuth();
    setUser(null);
    window.location.reload();
  }

  return (
    <header
      style={{
        background: "var(--bg-surface)",
        borderBottom: "1px solid var(--border)",
      }}
      className="px-6 py-3 flex items-center justify-between"
    >
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          <div
            style={{
              background: "linear-gradient(135deg, #3b82f6, #8b5cf6)",
              boxShadow: "0 0 12px rgba(59,130,246,0.4)",
            }}
            className="w-7 h-7 rounded-lg flex items-center justify-center"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="white">
              <path d="M3 3h18v2H3V3zm0 8h18v2H3v-2zm0 8h18v2H3v-2z" opacity="0.3" />
              <path d="M7 6l5-3 5 3v12l-5 3-5-3V6z" />
            </svg>
          </div>
          <span
            style={{
              background: "linear-gradient(90deg, #e2e8f0, #94a3b8)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
            }}
            className="font-bold text-base tracking-tight"
          >
            CryptoEngine
          </span>
        </div>
        <div
          style={{ background: "var(--border)", width: "1px", height: "16px" }}
        />
        <div className="flex items-center gap-1.5">
          <span
            style={{ background: "var(--green)", boxShadow: "0 0 6px var(--green)" }}
            className="w-1.5 h-1.5 rounded-full"
          />
          <span style={{ color: "var(--text-secondary)" }} className="text-xs">
            Live
          </span>
        </div>
      </div>

      <div>
        {user ? (
          <div className="flex items-center gap-3">
            <span style={{ color: "var(--text-secondary)" }} className="text-xs">
              {user.email}
            </span>
            <button
              onClick={handleLogout}
              style={{
                border: "1px solid var(--border)",
                color: "var(--text-secondary)",
                background: "transparent",
              }}
              className="text-xs px-3 py-1.5 rounded-lg hover:border-slate-500 hover:text-white transition-all duration-150"
            >
              Logout
            </button>
          </div>
        ) : (
          <button
            onClick={onAuthRequired}
            style={{
              background: "linear-gradient(135deg, #3b82f6, #6366f1)",
              boxShadow: "0 0 16px rgba(99,102,241,0.25)",
            }}
            className="text-sm text-white px-4 py-1.5 rounded-lg font-medium hover:opacity-90 transition-opacity duration-150"
          >
            Login / Sign Up
          </button>
        )}
      </div>
    </header>
  );
}
