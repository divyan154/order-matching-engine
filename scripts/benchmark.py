"""
Benchmark script — measures throughput and latency of the matching engine.

Usage:
    python scripts/benchmark.py                    # 10k orders, localhost
    python scripts/benchmark.py --url https://...  # run against production
    python scripts/benchmark.py --orders 1000      # smaller run

Requires server running with a valid DB connection.
"""

import argparse
import asyncio
import statistics
import time

import httpx


async def submit_order(client: httpx.AsyncClient, i: int) -> float:
    order = {
        "symbol": "BTCUSDT",
        "side": "buy" if i % 2 == 0 else "sell",
        "type": "limit",
        # Alternating prices around 50000 to generate lots of trades
        "price": 50000.0 + (i % 10) - 5,
        "quantity": 0.01,
    }
    start = time.perf_counter()
    r = await client.post("/orders", json=order)
    elapsed = time.perf_counter() - start
    r.raise_for_status()
    return elapsed


async def run(base_url: str, num_orders: int, concurrency: int):
    print(f"\nBenchmark: {num_orders} orders | concurrency={concurrency} | target={base_url}")
    print("-" * 60)

    latencies: list[float] = []
    errors = 0
    semaphore = asyncio.Semaphore(concurrency)

    async def bounded(i: int):
        nonlocal errors
        async with semaphore:
            try:
                lat = await submit_order(client, i)
                latencies.append(lat)
            except Exception as e:
                errors += 1

    async with httpx.AsyncClient(base_url=base_url, timeout=30) as client:
        # Warmup
        print("Warming up (50 orders)...")
        await asyncio.gather(*[bounded(i) for i in range(50)])
        latencies.clear()

        # Actual benchmark
        print(f"Running {num_orders} orders...")
        wall_start = time.perf_counter()
        await asyncio.gather(*[bounded(i) for i in range(num_orders)])
        wall_end = time.perf_counter()

    total_time = wall_end - wall_start
    success = len(latencies)
    throughput = success / total_time

    print("\nResults:")
    print(f"  Total orders:   {num_orders}")
    print(f"  Successful:     {success}")
    print(f"  Errors:         {errors}")
    print(f"  Total time:     {total_time:.2f}s")
    print(f"  Throughput:     {throughput:.0f} orders/sec")

    if latencies:
        sorted_lat = sorted(latencies)
        print(f"  Avg latency:    {statistics.mean(latencies) * 1000:.1f}ms")
        print(f"  Median (P50):   {statistics.median(latencies) * 1000:.1f}ms")
        print(f"  P95:            {sorted_lat[int(len(sorted_lat) * 0.95)] * 1000:.1f}ms")
        print(f"  P99:            {sorted_lat[int(len(sorted_lat) * 0.99)] * 1000:.1f}ms")
        print(f"  Min:            {min(latencies) * 1000:.1f}ms")
        print(f"  Max:            {max(latencies) * 1000:.1f}ms")

    print()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8000")
    parser.add_argument("--orders", type=int, default=10_000)
    parser.add_argument("--concurrency", type=int, default=50)
    args = parser.parse_args()

    asyncio.run(run(args.url, args.orders, args.concurrency))


if __name__ == "__main__":
    main()
