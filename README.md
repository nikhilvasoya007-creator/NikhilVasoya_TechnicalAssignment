# Sales Order & Inventory Management — Savyant Systems Technical Assignment

A Flask + MySQL web app for a small trading company to manage customers,
products, multi-item sales orders, stock, and sales/stock reports.

## Tech stack
- Python 3.14, Flask 3.1.3
- MySQL 8.0 (MySQL Workbench / Local instance MySQL80)
- HTML / CSS / JavaScript (fetch API, no framework)
- bcrypt, mysql-connector-python, python-dotenv, pytest

## Setup
1. Create the database and load the schema + sample data in MySQL Workbench:
   Run schema.sql, then run seed.sql
2. Copy .env.example to .env and set your real MySQL password in it:
   DB_HOST=localhost
   DB_USER=root
   DB_PASSWORD=your-password
   DB_NAME=sales_inventory
   SECRET_KEY=change-me-in-production
3. Install dependencies:
   python -m pip install -r requirements.txt
4. Run the app:
   python app.py
   Open http://127.0.0.1:5000

## Sample accounts
- Admin: admin@savyant.local / admin123
- Sales User: sales@savyant.local / sales123

Admin can manage customers/products, adjust stock, manage all orders and
view reports. A Sales User can view active customers/products and create /
manage only their own orders.

## Features
- Login/logout, role-based access enforced on the backend
- Customer and product CRUD with search/filter; delete blocked if referenced
  by an order (deactivate instead); unique product code; no negative price/stock
- Multi-item orders: backend-generated order number, product price copied
  from the database at order time, no duplicate product in one order,
  discount 0-20%, all totals calculated on the backend
  (subtotal, discount amount, grand total, rounded to 2 decimals)
- Order flow Draft -> Confirmed / Cancelled; Confirm checks all stock first
  and deducts in one transaction; Confirm/Cancel are idempotent
  (repeat confirm does not deduct again, repeat cancel does not restore again)
- Admin stock adjustment with mandatory reason and a stock movement record
- Reports (Confirmed orders only): Customer Sales Summary, Product Sales
  Summary, Low Stock Report, Stock Movement History
- CSV product import (Admin only, all-or-nothing): see data/products_valid.csv
  and data/products_invalid.csv
- REST API: see docs/api.md
- 5 standalone SQL queries: see docs/sql_queries.sql
- Debugging exercise: see debugging.py and docs/debugging.md

## Tests
Run: python -m pytest tests/ -v
16 tests: 7 for the debugging function, 9 for the app (multi-item order
with discount, zero/negative quantity, discount outside 0-20%, confirm
with sufficient/insufficient stock, repeated confirm, cancel with stock
restore, Sales User accessing another user's order, CSV with an invalid row).
Tests use a separate database sales_inventory_test, created and dropped
by the test fixture. The real sales_inventory database is untouched.

## Project structure
app.py - Flask app: routes, API, business logic
schema.sql - Database schema (6 tables)
seed.sql - Sample users, customers, products
templates/ - HTML pages
docs/api.md - API documentation
docs/sql_queries.sql - 5 standalone report queries
docs/debugging.md - Debugging exercise explanation
debugging.py - Corrected calculate_order_total()
data/ - Valid + invalid CSV samples
tests/ - pytest tests

## Incomplete items
None. All 14 parts of the assignment are implemented.
