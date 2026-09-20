"""Fail-fast data-quality checks for canonical processed tables."""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from src.config import PROCESSED_DIR

logger = logging.getLogger(__name__)


class QualityError(AssertionError):
    pass


def _require(frame: pd.DataFrame, columns: list[str], table: str) -> None:
    missing = set(columns) - set(frame.columns)
    if missing:
        raise QualityError(f"{table} missing required columns: {sorted(missing)}")
    nulls = frame[columns].isna().sum()
    bad = nulls[nulls > 0]
    if not bad.empty:
        raise QualityError(f"{table} has null required values: {bad.to_dict()}")


def run_quality_checks(tables: dict[str, pd.DataFrame]) -> dict:
    orders, customers, items = tables["orders"], tables["customers"], tables["order_items"]
    _require(orders, ["order_id", "customer_id", "order_date"], "orders")
    _require(customers, ["customer_id"], "customers")
    _require(items, ["order_id", "quantity", "price"], "order_items")
    if orders["order_id"].duplicated().any():
        raise QualityError("orders.order_id must be unique")
    if not (items["quantity"] > 0).all():
        raise QualityError("order_items.quantity must be > 0")
    if not (items["price"] >= 0).all():
        raise QualityError("order_items.price must be >= 0")
    unknown_customers = set(orders.customer_id) - set(customers.customer_id)
    if unknown_customers:
        raise QualityError(f"orders contains {len(unknown_customers)} unknown customer_id values")
    today = pd.Timestamp(datetime.now(timezone.utc).date())
    if (pd.to_datetime(orders.order_date) > today).any():
        raise QualityError("orders.order_date cannot be in the future")
    return {"status": "passed", "checked_at": datetime.now(timezone.utc).isoformat(), "rows": {k: len(v) for k, v in tables.items()}}


def check_processed(processed_dir: Path = PROCESSED_DIR) -> dict:
    tables = {name: pd.read_parquet(processed_dir / f"{name}.parquet") for name in ("orders", "customers", "order_items", "products", "payments")}
    report = run_quality_checks(tables)
    (processed_dir / "quality_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    logger.info("Quality checks passed: %s", report["rows"])
    return report


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    check_processed()

