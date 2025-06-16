import http from "k6/http";

export const options = {
  vus: 1000, // Number of virtual users
  duration: "1s", // Total duration
};

export default function () {
  const url = "http://127.0.0.1:8000/submit_order"; // Replace with your actual endpoint

  const payload = JSON.stringify({
    symbol: "BTCUSDT",
      side: "buy",
    type: "limit",
    quantity: 1,
    price: 45000,
  });

  const params = {
    headers: {
      "Content-Type": "application/json",
    },
  };

  http.post(url, payload, params);
}
