"""Create deterministic, synthetic CSV input suitable for the MVP demo."""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import PROJECT_ROOT, RAW_DIR


def generate(output_dir: Path = RAW_DIR, order_count: int = 3000, seed: int = 42) -> None:
    rng = np.random.default_rng(seed)
    output_dir.mkdir(parents=True, exist_ok=True)
    customer_count, product_count = 800, 120
    customers = pd.DataFrame({"customer_id": [f"C{i:04d}" for i in range(customer_count)],
        "customer_name": [f"Customer {i:04d}" for i in range(customer_count)],
        "region": rng.choice(["North", "Central", "South"], customer_count),
        "signup_date": pd.Timestamp("2023-01-01") + pd.to_timedelta(rng.integers(0, 700, customer_count), unit="D")})
    products = pd.DataFrame({"product_id": [f"P{i:03d}" for i in range(product_count)],
        "product_name": [f"Product {i:03d}" for i in range(product_count)],
        "category": rng.choice(["Electronics", "Home", "Fashion", "Beauty"], product_count),
        "price": rng.integers(5, 500, product_count)})
    order_dates = pd.Timestamp("2024-01-01") + pd.to_timedelta(rng.integers(0, 850, order_count), unit="D")
    orders = pd.DataFrame({"order_id": [f"O{i:06d}" for i in range(order_count)],
        "customer_id": rng.choice(customers.customer_id, order_count), "order_date": order_dates,
        "order_status": rng.choice(["completed", "completed", "completed", "cancelled", "returned"], order_count)})
    order_items = pd.DataFrame({"order_id": np.repeat(orders.order_id.to_numpy(), rng.integers(1, 5, order_count))})
    order_items["product_id"] = rng.choice(products.product_id, len(order_items))
    order_items["quantity"] = rng.integers(1, 4, len(order_items))
    prices = products.set_index("product_id").price
    order_items["price"] = order_items.product_id.map(prices).astype(float)
    payments = orders[["order_id"]].copy()
    payments["payment_value"] = payments.order_id.map((order_items.quantity * order_items.price).groupby(order_items.order_id).sum())
    payments["payment_installments"] = rng.integers(1, 7, order_count)
    for name, frame in {"orders": orders, "order_items": order_items, "customers": customers, "products": products, "payments": payments}.items():
        frame.to_csv(output_dir / f"{name}.csv", index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=RAW_DIR)
    parser.add_argument("--orders", type=int, default=3000)
    args = parser.parse_args()
    generate(args.out, args.orders)
