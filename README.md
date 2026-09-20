# E-commerce Data Platform

MVP data-engineering project: raw e-commerce CSVs are normalized to Parquet, checked for data quality, modelled as a star schema, then loaded into PostgreSQL for KPI queries and a small Streamlit dashboard.

## Architecture

```text
data/raw CSV (immutable)
  -> ingest.py -> data/processed Parquet
  -> quality.py (fail fast + quality_report.json)
  -> transform.py (dimensions + facts)
  -> load.py -> PostgreSQL -> SQL / Streamlit
```

`fact_orders` has one row per business transaction and measures such as `order_revenue`; `fact_order_items` has one row per product line and measures such as `quantity` and `line_revenue`. Dimensions hold reusable descriptive attributes: customer/region, product/category, and calendar properties. This separation prevents descriptive data from being repeated through analytic facts and makes KPI joins predictable.

## Dataset contract

Place five CSVs in `data/raw/`: `orders`, `order_items`, `customers`, `products`, and `payments`. Expected canonical fields are:

- `orders`: `order_id`, `customer_id`, `order_date`, optional `order_status`
- `order_items`: `order_id`, `product_id`, `quantity`, `price`
- `customers`: `customer_id`, optional `customer_name`, `region`, `signup_date`
- `products`: `product_id`, optional `product_name`, `category`, `price`
- `payments`: `order_id`, `payment_value`, optional `payment_installments`

Headers are converted to snake_case and configured date/numeric fields are cast during ingestion. Source CSVs are read only; generated Parquet is overwritten on a rerun, so identical source produces the same logical output.

To create deterministic synthetic data (3,000 orders) for a demo:

```powershell
python -m src.generate_sample_data
```

Use `--out data/sample` to create a small distributable fixture instead of the raw input folder.

## Run locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
docker compose up -d
python -m src.generate_sample_data
python -m src.pipeline
streamlit run dashboard/app.py
```

The full pipeline can also be run step-by-step with `python -m src.ingest`, `python -m src.quality`, `python -m src.transform`, and `python -m src.load`. Execute checks with `pytest`.

## Star schema

```text
dim_customer ─┐
dim_product ──┼── fact_order_items ── fact_orders ── dim_date
              └─────────────────────────────────────┘
```

The actual foreign keys are `fact_orders.customer_id`, `fact_orders.date_key`, `fact_order_items.order_id`, and `fact_order_items.product_id`.

## Data-quality rules

- No null `order_id`, `customer_id`, or `order_date` in orders.
- `orders.order_id` is unique.
- `quantity > 0` and `price >= 0` in order items.
- Each order customer exists in customers.
- Order dates cannot be in the future.

Severe violations raise `QualityError`, preventing transform/load. The successful check report is stored as `data/processed/quality_report.json` and shown in the dashboard.

## KPIs

[`sql/analytics.sql`](sql/analytics.sql) includes monthly revenue, order count/AOV, top products, repeat-customer rate, regional revenue, and cancellation/return rate.

## Next iterations

Add Prefect retries/scheduling around `src.pipeline`, dbt models/tests, CI, warehouse constraints and migrations, data lineage, and a LangGraph analytics assistant. Add a dashboard screenshot here after launching the local Streamlit app.

