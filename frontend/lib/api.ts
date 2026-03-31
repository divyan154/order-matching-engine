import { authHeaders } from "./auth";

const BASE = "/api";

async function request(path: string, options: RequestInit = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...authHeaders(), ...(options.headers || {}) },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Request failed");
  }
  return res.json();
}

// Auth
export const signup = (email: string, password: string) =>
  request("/auth/signup", { method: "POST", body: JSON.stringify({ email, password }) });

export const login = (email: string, password: string) =>
  request("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) });

// Orders
export const submitOrder = (order: {
  symbol: string;
  side: string;
  type: string;
  price: number;
  quantity: number;
}) => request("/orders", { method: "POST", body: JSON.stringify(order) });

export const getOrder = (id: string) => request(`/orders/${id}`);

export const cancelOrder = (id: string) =>
  request(`/orders/${id}`, { method: "DELETE" });

// Market data
export const getOrderBook = (symbol: string, depth = 20) =>
  request(`/orderbook/${symbol}?depth=${depth}`);

export const getTrades = (symbol: string, limit = 30) =>
  request(`/trades/${symbol}?limit=${limit}`);
