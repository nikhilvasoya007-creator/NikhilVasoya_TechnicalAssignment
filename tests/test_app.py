import os
os.environ["DB_NAME"] = "sales_inventory_test"
from decimal import Decimal
import pytest
import mysql.connector
from app import app, calc_totals

ADMIN = {"email": "admin@savyant.local", "password": "admin123"}
SALES = {"email": "sales@savyant.local", "password": "sales123"}


def _conn(db=None):
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=db or os.getenv("DB_NAME", "sales_inventory_test"),
    )


@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    conn = _conn("mysql")
    cur = conn.cursor()
    cur.execute("DROP DATABASE IF EXISTS sales_inventory_test")
    cur.execute("CREATE DATABASE sales_inventory_test CHARACTER SET utf8mb4")
    conn.commit(); cur.close(); conn.close()
    conn = _conn()
    cur = conn.cursor()
    sql = open("schema.sql").read().split("USE sales_inventory;")[-1]
    for stmt in sql.split(";"):
        stmt = stmt.strip()
        if stmt:
            cur.execute(stmt)
    conn.commit(); cur.close(); conn.close()


    # seed minimal data via the app's own seed file logic
    import bcrypt
    conn = _conn()
    cur = conn.cursor()
    ah = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode()
    sh = bcrypt.hashpw(b"sales123", bcrypt.gensalt()).decode()
    cur.execute("INSERT INTO users (name, email, password_hash, role) VALUES (%s, %s, %s, 'Admin')", ("Admin User", ADMIN["email"], ah))
    cur.execute("INSERT INTO users (name, email, password_hash, role) VALUES (%s, %s, %s, 'Sales User')", ("Sales User", SALES["email"], sh))
    cur.execute("INSERT INTO customers (name, email, mobile, city, is_active) VALUES ('Raj Patel', 'raj@example.com', '9876543210', 'Ahmedabad', TRUE)")
    cur.execute("INSERT INTO products (product_code, name, category, price, stock_quantity, is_active) VALUES ('PRD-001', 'Keyboard', 'Accessories', 1500.00, 20, TRUE), ('PRD-002', 'Mouse', 'Accessories', 500.00, 50, TRUE)")
    conn.commit(); cur.close(); conn.close()
    yield
    conn = _conn("mysql")
    cur = conn.cursor()
    cur.execute("DROP DATABASE IF EXISTS sales_inventory_test")
    conn.commit(); cur.close(); conn.close()


@pytest.fixture
def client():
    app.config["TESTING"] = True
    return app.test_client()


def login(client, creds):
    return client.post("/login", data=creds, follow_redirects=True)


def make_draft_order(client):
    login(client, ADMIN)
    r = client.post("/orders/add", data={
        "customer_id": "1", "discount_percentage": "10",
        "product_id": ["1", "2"], "quantity": ["2", "3"],
    }, follow_redirects=True)
    return r


# 1. Multi-item order with discount — correct subtotal / grand total
def test_multi_item_order_with_discount():
    items = [{"qty": 2, "rate": Decimal("1500")}, {"qty": 3, "rate": Decimal("500")}]
    sub, disc, grand = calc_totals(items, Decimal("10"))
    assert sub == Decimal("4500.00") and disc == Decimal("450.00") and grand == Decimal("4050.00")


# 2. Zero / negative quantity rejected (via the order form)
def test_zero_quantity_rejected(client):
    login(client, ADMIN)
    r = client.post("/orders/add", data={
        "customer_id": "1", "discount_percentage": "0",
        "product_id": ["1"], "quantity": ["0"],
    }, follow_redirects=True)
    assert b"Quantity must be a whole number above 0" in r.data


# 3. Discount outside 0-20% rejected
def test_discount_outside_range_rejected(client):
    login(client, ADMIN)
    r = client.post("/orders/add", data={
        "customer_id": "1", "discount_percentage": "25",
        "product_id": ["1"], "quantity": ["1"],
    }, follow_redirects=True)
    assert b"Discount must be 0 to 20%" in r.data


# 4. Confirm with sufficient stock — confirmed + deducted
def test_confirm_with_sufficient_stock(client):
    make_draft_order(client)
    r = client.post("/orders/1/confirm", follow_redirects=True)
    assert b"Order confirmed" in r.data
    conn = _conn(); cur = conn.cursor(dictionary=True)
    cur.execute("SELECT stock_quantity FROM products WHERE id = 1")
    assert cur.fetchone()["stock_quantity"] == 18
    cur.execute("SELECT status FROM sales_orders WHERE id = 1")
    assert cur.fetchone()["status"] == "Confirmed"
    cur.close(); conn.close()


# 5. Confirm with one insufficient item — no stock / status change
def test_confirm_with_insufficient_stock(client):
    login(client, ADMIN)
    client.post("/orders/add", data={
        "customer_id": "1", "discount_percentage": "0",
        "product_id": ["1"], "quantity": ["999"],
    }, follow_redirects=True)
    r = client.post("/orders/2/confirm", follow_redirects=True)
    assert b"Insufficient stock" in r.data
    conn = _conn(); cur = conn.cursor(dictionary=True)
    cur.execute("SELECT stock_quantity FROM products WHERE id = 1")
    assert cur.fetchone()["stock_quantity"] == 18
    cur.execute("SELECT status FROM sales_orders WHERE id = 2")
    assert cur.fetchone()["status"] == "Draft"
    cur.close(); conn.close()


# 6. Repeated confirm — no extra deduction
def test_repeated_confirm_no_extra_deduction(client):
    login(client, ADMIN)
    r = client.post("/orders/1/confirm", follow_redirects=True)
    assert b"Only a Draft order can be confirmed" in r.data
    conn = _conn(); cur = conn.cursor(dictionary=True)
    cur.execute("SELECT stock_quantity FROM products WHERE id = 1")
    assert cur.fetchone()["stock_quantity"] == 18
    cur.close(); conn.close()


# 7. Cancel Confirmed — stock restored once
def test_cancel_confirmed_restores_stock_once(client):
    login(client, ADMIN)
    r = client.post("/orders/1/cancel", follow_redirects=True)
    assert b"Order cancelled" in r.data
    conn = _conn(); cur = conn.cursor(dictionary=True)
    cur.execute("SELECT stock_quantity FROM products WHERE id = 1")
    assert cur.fetchone()["stock_quantity"] == 20
    cur.close(); conn.close()


# 8. Sales User accessing another user's order — denied
def test_sales_user_cannot_view_others_order(client):
    login(client, SALES)
    r = client.get("/orders/1", follow_redirects=True)
    assert b"cannot view another user" in r.data


# 9. CSV with invalid row — nothing imported
def test_csv_invalid_row_imports_nothing(client):
    login(client, ADMIN)
    import io
    bad = b"product_code,product_name,category,price,stock_quantity,status\nPRD-999,New,Accessories,100.00,5,Active\nPRD-001,Dup,Accessories,100.00,5,Active\n"
    r = client.post("/products/import", data={"file": (io.BytesIO(bad), "bad.csv")},
                    content_type="multipart/form-data", follow_redirects=True)
    assert b"nothing was imported" in r.data or b"already exists" in r.data
    conn = _conn(); cur = conn.cursor(dictionary=True)
    cur.execute("SELECT COUNT(*) AS c FROM products WHERE product_code = 'PRD-999'")
    assert cur.fetchone()["c"] == 0
    cur.close(); conn.close()
