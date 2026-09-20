from pathlib import Path
import os

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://ecommerce:ecommerce@localhost:5432/ecommerce",
)

# Canonical columns expected by the MVP. Extra source columns are preserved.
TABLE_SCHEMAS = {
    "orders": {
        "dates": ["order_date", "order_purchase_timestamp", "order_approved_at", "order_delivered_at"],
        "integers": [],
        "numbers": [],
    },
    "order_items": {
        "dates": [],
        "integers": ["quantity"],
        "numbers": ["price", "freight_value"],
    },
    "customers": {
        "dates": ["signup_date", "customer_since"],
        "integers": [],
        "numbers": [],
    },
    "products": {
        "dates": [],
        "integers": [],
        "numbers": ["price"],
    },
    "payments": {
        "dates": [],
        "integers": ["payment_installments"],
        "numbers": ["payment_value"],
    },
}

REQUIRED_TABLES = tuple(TABLE_SCHEMAS)

