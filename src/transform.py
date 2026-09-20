"""Build a compact star schema from cleaned Parquet sources."""
import logging
from pathlib import Path

import pandas as pd

from src.config import PROCESSED_DIR

logger = logging.getLogger(__name__)


def _column(frame: pd.DataFrame, names: list[str], default=None):
    for name in names:
        if name in frame:
            return frame[name]
    return pd.Series(default, index=frame.index)


def build_star_schema(processed_dir: Path = PROCESSED_DIR) -> dict[str, pd.DataFrame]:
    orders = pd.read_parquet(processed_dir / "orders.parquet")
    customers = pd.read_parquet(processed_dir / "customers.parquet")
    products = pd.read_parquet(processed_dir / "products.parquet")
    items = pd.read_parquet(processed_dir / "order_items.parquet")

    dim_customer = pd.DataFrame({
        "customer_id": customers.customer_id,
        "customer_name": _column(customers, ["customer_name", "name"]),
        "region": _column(customers, ["region", "customer_state", "state"]),
        "signup_date": pd.to_datetime(_column(customers, ["signup_date", "customer_since"]), errors="coerce"),
    }).drop_duplicates("customer_id")
    dim_product = pd.DataFrame({
        "product_id": products.product_id,
        "product_name": _column(products, ["product_name", "name"]),
        "category": _column(products, ["category", "product_category_name"]),
        "list_price": pd.to_numeric(_column(products, ["price", "list_price"]), errors="coerce"),
    }).drop_duplicates("product_id")

    order_dates = pd.to_datetime(orders.order_date).dt.normalize()
    dim_date = pd.DataFrame({"date": order_dates.drop_duplicates().sort_values()})
    dim_date["date_key"] = dim_date.date.dt.strftime("%Y%m%d").astype(int)
    dim_date["year"] = dim_date.date.dt.year
    dim_date["quarter"] = "Q" + dim_date.date.dt.quarter.astype(str)
    dim_date["month"] = dim_date.date.dt.month
    dim_date["month_name"] = dim_date.date.dt.month_name()

    fact_orders = pd.DataFrame({
        "order_id": orders.order_id,
        "customer_id": orders.customer_id,
        "order_date": order_dates,
        "date_key": order_dates.dt.strftime("%Y%m%d").astype(int),
        "order_status": _column(orders, ["order_status", "status"], "completed"),
    })
    item_values = pd.to_numeric(items.quantity) * pd.to_numeric(items.price)
    revenue = pd.DataFrame({"order_id": items.order_id, "item_revenue": item_values}).groupby("order_id", as_index=False).item_revenue.sum()
    fact_orders = fact_orders.merge(revenue, on="order_id", how="left").rename(columns={"item_revenue": "order_revenue"})
    fact_orders["order_revenue"] = fact_orders.order_revenue.fillna(0.0)

    fact_order_items = pd.DataFrame({
        "order_item_key": range(1, len(items) + 1),
        "order_id": items.order_id,
        "product_id": items.product_id,
        "quantity": pd.to_numeric(items.quantity),
        "unit_price": pd.to_numeric(items.price),
    })
    fact_order_items["line_revenue"] = fact_order_items.quantity * fact_order_items.unit_price

    tables = {"dim_customer": dim_customer, "dim_product": dim_product, "dim_date": dim_date,
              "fact_orders": fact_orders, "fact_order_items": fact_order_items}
    for name, frame in tables.items():
        frame.to_parquet(processed_dir / f"{name}.parquet", index=False)
        logger.info("Built %s (%d rows)", name, len(frame))
    return tables


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    build_star_schema()

