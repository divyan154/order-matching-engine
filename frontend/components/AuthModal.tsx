"use client";

import { useState } from "react";
import { login, signup } from "@/lib/api";
import { saveAuth } from "@/lib/auth";

interface Props {
  onSuccess: () => void;
  onClose: () => void;
}

export default function AuthModal({ onSuccess, onClose }: Props) {
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const fn = mode === "login" ? login : signup;
      const data = await fn(email, password);
      saveAuth(data.access_token, data.user_id, data.email);
      onSuccess();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  const inputStyle: React.CSSProperties = {
    background: "var(--bg-base)",
    border: "1px solid var(--border)",
    color: "var(--text-primary)",
    borderRadius: "8px",
    outline: "none",
    width: "100%",
    padding: "11px 12px",
    fontSize: "14px",
    transition: "border-color 0.15s",
  };

  return (
    <div
      className="fixed inset-0 flex items-center justify-center z-50"
      style={{ background: "rgba(0,0,0,0.75)", backdropFilter: "blur(6px)" }}
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div
        style={{
          background: "var(--bg-surface)",
          border: "1px solid var(--border)",
          borderRadius: "16px",
          width: "100%",
          maxWidth: "360px",
          boxShadow: "0 24px 48px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.03)",
          overflow: "hidden",
        }}
      >
        {/* Modal header */}
        <div
          style={{ borderBottom: "1px solid var(--border)", padding: "16px 20px" }}
          className="flex items-center justify-between"
        >
          <div>
            <div
              style={{
                background: "linear-gradient(135deg, #3b82f6, #8b5cf6)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
              }}
              className="font-bold text-sm"
            >
              CryptoEngine
            </div>
            <div className="text-base font-semibold text-white mt-0.5">
              {mode === "login" ? "Welcome back" : "Create account"}
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              background: "var(--bg-base)",
              border: "1px solid var(--border)",
              color: "var(--text-secondary)",
              borderRadius: "8px",
              width: "32px",
              height: "32px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              cursor: "pointer",
              fontSize: "16px",
            }}
          >
            ✕
          </button>
        </div>

        <div style={{ padding: "20px" }}>
          <form onSubmit={handleSubmit} className="space-y-3">
            <input
              type="email"
              placeholder="Email address"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              style={inputStyle}
              onFocus={(e) => (e.target.style.borderColor = "var(--accent)")}
              onBlur={(e) => (e.target.style.borderColor = "var(--border)")}
            />
            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              style={inputStyle}
              onFocus={(e) => (e.target.style.borderColor = "var(--accent)")}
              onBlur={(e) => (e.target.style.borderColor = "var(--border)")}
            />

            {error && (
              <div
                style={{
                  background: "rgba(239,68,68,0.08)",
                  border: "1px solid rgba(239,68,68,0.25)",
                  borderRadius: "6px",
                  padding: "8px 10px",
                  color: "var(--red)",
                  fontSize: "12px",
                }}
              >
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              style={{
                background: loading
                  ? "rgba(59,130,246,0.3)"
                  : "linear-gradient(135deg, #3b82f6, #6366f1)",
                boxShadow: loading ? "none" : "0 4px 14px rgba(99,102,241,0.3)",
                borderRadius: "8px",
                color: "white",
                width: "100%",
                padding: "12px",
                fontSize: "14px",
                fontWeight: "600",
                border: "none",
                cursor: loading ? "not-allowed" : "pointer",
                transition: "all 0.15s",
                marginTop: "4px",
              }}
            >
              {loading ? "..." : mode === "login" ? "Sign in" : "Create Account"}
            </button>
          </form>

          <p className="text-center mt-4 text-xs" style={{ color: "var(--text-secondary)" }}>
            {mode === "login" ? "Don't have an account?" : "Already have an account?"}{" "}
            <button
              onClick={() => {
                setMode(mode === "login" ? "signup" : "login");
                setError("");
              }}
              style={{ color: "var(--accent)", background: "none", border: "none", cursor: "pointer" }}
              className="hover:underline font-medium"
            >
              {mode === "login" ? "Sign up" : "Sign in"}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}
