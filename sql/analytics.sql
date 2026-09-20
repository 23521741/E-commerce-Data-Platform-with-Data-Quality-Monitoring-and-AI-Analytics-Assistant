-- 1. Monthly revenue and orders
SELECT date_trunc('month', order_date)::date AS month,
       COUNT(*) AS orders,
       ROUND(SUM(order_revenue)::numeric, 2) AS revenue,
       ROUND(AVG(order_revenue)::numeric, 2) AS aov
FROM fact_orders
WHERE order_status NOT IN ('cancelled', 'returned')
GROUP BY 1 ORDER BY 1;

-- 2. Top products by revenue
SELECT p.category, p.product_name, SUM(i.quantity) AS units,
       ROUND(SUM(i.line_revenue)::numeric, 2) AS revenue
FROM fact_order_items i JOIN dim_product p USING (product_id)
GROUP BY 1, 2 ORDER BY revenue DESC LIMIT 10;

-- 3. Returning-customer rate
WITH customer_orders AS (
  SELECT customer_id, COUNT(*) AS order_count FROM fact_orders
  WHERE order_status NOT IN ('cancelled', 'returned') GROUP BY 1
)
SELECT ROUND(100.0 * COUNT(*) FILTER (WHERE order_count > 1) / NULLIF(COUNT(*), 0), 2) AS returning_customer_rate_pct
FROM customer_orders;

-- 4. Revenue by region
SELECT c.region, ROUND(SUM(o.order_revenue)::numeric, 2) AS revenue
FROM fact_orders o JOIN dim_customer c USING (customer_id)
WHERE o.order_status NOT IN ('cancelled', 'returned')
GROUP BY 1 ORDER BY revenue DESC;

-- 5. Cancellation / return rate
SELECT order_status, COUNT(*) AS orders,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS order_rate_pct
FROM fact_orders GROUP BY 1 ORDER BY orders DESC;

