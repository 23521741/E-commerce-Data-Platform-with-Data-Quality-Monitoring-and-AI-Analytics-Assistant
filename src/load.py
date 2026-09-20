"""Load star-schema Parquet tables into PostgreSQL."""
import logging
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

from src.config import DATABASE_URL, PROCESSED_DIR

logger = logging.getLogger(__name__)
STAR_TABLES = ("dim_customer", "dim_product", "dim_date", "fact_orders", "fact_order_items")


def load_to_postgres(database_url: str = DATABASE_URL, processed_dir: Path = PROCESSED_DIR) -> None:
    engine = create_engine(database_url)
    # replace is deliberate: every run is a complete, reproducible MVP snapshot.
    with engine.begin() as connection:
        for table in STAR_TABLES:
            frame = pd.read_parquet(processed_dir / f"{table}.parquet")
            frame.to_sql(table, connection, if_exists="replace", index=False, method="multi")
            logger.info("Loaded %s (%d rows)", table, len(frame))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_fact_orders_date ON fact_orders(order_date)"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_fact_order_items_product ON fact_order_items(product_id)"))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    load_to_postgres()

