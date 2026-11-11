# API Documentation — Savyant Sales Order App

All API calls require login (session cookie from `/login`).
Admin sees all orders; a Sales User sees only their own orders (403 otherwise).
Errors are JSON: `{"error": "message"}` — no passwords, secrets or tracebacks.

## GET /api/products?q=&page=
Search active products, 10 per page.
- 200: `{"page": 1, "per_page": 10, "total": 5, "products": [{"id": 1, "product_code": "PRD-001", "name": "Keyboard", "category": "Accessories", "price": 1500.0, "stock_quantity": 20}]}`
- Example: `GET /api/products?q=Mouse`

## POST /api/orders
Create a Draft order. Rates are taken from the database, never from the request.
- Request JSON:
```json
{"customer_id": 1, "discount_percentage": 10,
 "items": [{"product_id": 1, "quantity": 2}, {"product_id": 2, "quantity": 3}]}
