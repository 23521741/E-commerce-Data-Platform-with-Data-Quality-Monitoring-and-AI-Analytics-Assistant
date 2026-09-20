import json
import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parents[1]
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://ecommerce:ecommerce@localhost:5432/ecommerce")

st.set_page_config(page_title="E-commerce KPIs", layout="wide")
st.title("E-commerce data platform — KPI dashboard")

try:
    engine = create_engine(DATABASE_URL)
    base = pd.read_sql("""SELECT o.order_id, o.order_date, o.order_revenue, o.order_status,
                         c.region, p.category, p.product_name, i.quantity, i.line_revenue
                         FROM fact_orders o JOIN dim_customer c USING(customer_id)
                         JOIN fact_order_items i USING(order_id) JOIN dim_product p USING(product_id)""", engine)
except Exception as exc:
    st.error(f"Cannot query PostgreSQL. Start Docker and run the pipeline first. ({exc})")
    st.stop()

base["order_date"] = pd.to_datetime(base.order_date)
with st.sidebar:
    st.header("Filters")
    dates = st.date_input("Date range", (base.order_date.min().date(), base.order_date.max().date()))
    categories = st.multiselect("Category", sorted(base.category.dropna().unique()))
    regions = st.multiselect("Region", sorted(base.region.dropna().unique()))

filtered = base[(base.order_date.dt.date >= dates[0]) & (base.order_date.dt.date <= dates[-1])]
if categories: filtered = filtered[filtered.category.isin(categories)]
if regions: filtered = filtered[filtered.region.isin(regions)]
valid = filtered[~filtered.order_status.isin(["cancelled", "returned"])]
orders = valid[["order_id", "order_revenue"]].drop_duplicates()
cols = st.columns(4)
cols[0].metric("Revenue", f"${orders.order_revenue.sum():,.0f}")
cols[1].metric("Orders", f"{len(orders):,}")
cols[2].metric("AOV", f"${orders.order_revenue.mean():,.2f}" if len(orders) else "$0")
cols[3].metric("Cancelled / returned", f"{100 * filtered.order_status.isin(['cancelled', 'returned']).mean():.1f}%")

monthly = valid[["order_id", "order_date", "order_revenue"]].drop_duplicates("order_id").groupby(pd.Grouper(key="order_date", freq="MS")).order_revenue.sum().reset_index()
st.plotly_chart(px.line(monthly, x="order_date", y="order_revenue", title="Revenue over time"), use_container_width=True)
top = valid.groupby("product_name", as_index=False).line_revenue.sum().nlargest(10, "line_revenue")
st.plotly_chart(px.bar(top, x="product_name", y="line_revenue", title="Top products"), use_container_width=True)

st.subheader("Latest data quality check")
report_path = ROOT / "data" / "processed" / "quality_report.json"
st.json(json.loads(report_path.read_text()) if report_path.exists() else {"status": "No report found"})
