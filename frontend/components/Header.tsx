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
    <header className="bg-gray-900 border-b border-gray-800 px-6 py-3 flex items-center justify-between">
      <div className="flex items-center gap-2">
        <span className="text-white font-bold text-lg">CryptoEngine</span>
        <span className="text-gray-500 text-sm">Order Matching</span>
      </div>

      <div>
        {user ? (
          <div className="flex items-center gap-3">
            <span className="text-gray-400 text-sm">{user.email}</span>
            <button
              onClick={handleLogout}
              className="text-xs text-gray-400 hover:text-white border border-gray-700 px-3 py-1 rounded"
            >
              Logout
            </button>
          </div>
        ) : (
          <button
            onClick={onAuthRequired}
            className="text-sm bg-blue-600 hover:bg-blue-700 text-white px-4 py-1.5 rounded"
          >
            Login / Sign Up
          </button>
        )}
      </div>
    </header>
  );
}
