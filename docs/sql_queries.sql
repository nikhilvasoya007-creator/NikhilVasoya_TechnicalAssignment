-- Savyant Sales Order & Inventory — 5 standalone SQL queries
-- Run in MySQL Workbench with: USE sales_inventory;
-- Q5 uses a placeholder :threshold — replace it with a number, e.g. 10.

-- Q1. Top 3 customers by Confirmed order grand total
SELECT c.id, c.name, c.email, SUM(o.grand_total) AS total_sales
FROM customers c
JOIN sales_orders o ON o.customer_id = c.id
WHERE o.status = 'Confirmed'
GROUP BY c.id, c.name, c.email
ORDER BY total_sales DESC
LIMIT 3;

-- Q2. Top 3 products by quantity sold in Confirmed orders
SELECT p.product_code, p.name, SUM(i.quantity) AS qty_sold
FROM products p
JOIN sales_order_items i ON i.product_id = p.id
JOIN sales_orders o ON o.id = i.sales_order_id
WHERE o.status = 'Confirmed'
GROUP BY p.id, p.product_code, p.name
ORDER BY qty_sold DESC
LIMIT 3;

-- Q3. Customers who never placed any order
SELECT c.id, c.name, c.email
FROM customers c
LEFT JOIN sales_orders o ON o.customer_id = c.id
WHERE o.id IS NULL;

-- Q4. Month-wise Confirmed sales by year and month
SELECT YEAR(o.order_date) AS sales_year, MONTH(o.order_date) AS sales_month,
       COUNT(*) AS order_count, SUM(o.grand_total) AS total_sales
FROM sales_orders o
WHERE o.status = 'Confirmed'
GROUP BY YEAR(o.order_date), MONTH(o.order_date)
ORDER BY sales_year, sales_month;

-- Q5. Products below a supplied stock threshold (replace :threshold, e.g. 10)
SELECT product_code, name, category, stock_quantity
FROM products
WHERE stock_quantity < 10
ORDER BY stock_quantity;
