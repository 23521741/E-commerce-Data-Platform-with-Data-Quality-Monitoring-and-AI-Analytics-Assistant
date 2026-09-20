import pandas as pd
import pytest

from src.quality import QualityError, run_quality_checks


def tables():
    return {
        "orders": pd.DataFrame({"order_id": ["o1"], "customer_id": ["c1"], "order_date": ["2024-01-01"]}),
        "customers": pd.DataFrame({"customer_id": ["c1"]}),
        "order_items": pd.DataFrame({"order_id": ["o1"], "quantity": [1], "price": [2.5]}),
        "products": pd.DataFrame(), "payments": pd.DataFrame(),
    }


def test_quality_passes_for_valid_data():
    assert run_quality_checks(tables())["status"] == "passed"


def test_quality_rejects_duplicate_order_id():
    bad = tables()
    bad["orders"] = pd.concat([bad["orders"], bad["orders"]])
    with pytest.raises(QualityError, match="unique"):
        run_quality_checks(bad)

