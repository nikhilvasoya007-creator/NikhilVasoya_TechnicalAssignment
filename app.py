from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
import mysql.connector
import bcrypt
import os
from dotenv import load_dotenv
from decimal import Decimal
from datetime import date
import csv
import io
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify



load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")

def get_db():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "sales_inventory")
    )

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        if session.get("role") != "Admin":
            flash("Admin access only.")
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return wrapper

@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        cur.close()
        conn.close()
        if user and bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
            session["user_id"] = user["id"]
            session["name"] = user["name"]
            session["role"] = user["role"]
            session["email"] = user["email"]
            return redirect(url_for("dashboard"))
        flash("Invalid email or password.")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT COUNT(*) AS c FROM customers")
    customers = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) AS c FROM products")
    products = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) AS c FROM sales_orders")
    orders = cur.fetchone()["c"]
    cur.close()
    conn.close()
    return render_template("dashboard.html",
                           name=session["name"], role=session["role"],
                           customers=customers, products=products, orders=orders)

# ---------- Customers (Part 4) ----------
@app.route("/customers")
@login_required
def customers_list():
    q = request.args.get("q", "").strip()
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    if q:
        like = f"%{q}%"
        cur.execute("SELECT * FROM customers WHERE name LIKE %s OR email LIKE %s OR city LIKE %s ORDER BY id",
                    (like, like, like))
    else:
        cur.execute("SELECT * FROM customers ORDER BY id")
    customers = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("customers.html", customers=customers, q=q)

@app.route("/customers/add", methods=["GET", "POST"])
@admin_required
def customers_add():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        mobile = request.form.get("mobile", "").strip()
        city = request.form.get("city", "").strip()
        if not name or not email:
            flash("Name and Email are required.")
            return render_template("customer_form.html", customer=None)
        conn = get_db()
        cur = conn.cursor()
        cur.execute("INSERT INTO customers (name, email, mobile, city, is_active) VALUES (%s, %s, %s, %s, TRUE)",
                    (name, email, mobile, city))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for("customers_list"))
    return render_template("customer_form.html", customer=None)

@app.route("/customers/<int:cid>/edit", methods=["GET", "POST"])
@admin_required
def customers_edit(cid):
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM customers WHERE id = %s", (cid,))
    customer = cur.fetchone()
    if not customer:
        cur.close(); conn.close()
        flash("Customer not found.")
        return redirect(url_for("customers_list"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        mobile = request.form.get("mobile", "").strip()
        city = request.form.get("city", "").strip()
        if not name or not email:
            flash("Name and Email are required.")
            cur.close(); conn.close()
            return render_template("customer_form.html", customer=customer)
        cur2 = conn.cursor()
        cur2.execute("UPDATE customers SET name=%s, email=%s, mobile=%s, city=%s WHERE id=%s",
                     (name, email, mobile, city, cid))
        conn.commit()
        cur2.close(); cur.close(); conn.close()
        return redirect(url_for("customers_list"))
    cur.close(); conn.close()
    return render_template("customer_form.html", customer=customer)

@app.route("/customers/<int:cid>/toggle", methods=["POST"])
@admin_required
def customers_toggle(cid):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE customers SET is_active = NOT is_active WHERE id = %s", (cid,))
    conn.commit()
    cur.close(); conn.close()
    return redirect(url_for("customers_list"))

@app.route("/customers/<int:cid>/delete", methods=["POST"])
@admin_required
def customers_delete(cid):
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT COUNT(*) AS c FROM sales_orders WHERE customer_id = %s", (cid,))
    used = cur.fetchone()["c"]
    if used > 0:
        cur.close(); conn.close()
        flash("Cannot delete — this customer has orders. Deactivate instead.")
        return redirect(url_for("customers_list"))
    cur2 = conn.cursor()
    cur2.execute("DELETE FROM customers WHERE id = %s", (cid,))
    conn.commit()
    cur2.close(); cur.close(); conn.close()
    return redirect(url_for("customers_list"))

# ---------- Products (Part 4) ----------
@app.route("/products")
@login_required
def products_list():
    q = request.args.get("q", "").strip()
    cat = request.args.get("category", "").strip()
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT DISTINCT category FROM products ORDER BY category")
    categories = [r["category"] for r in cur.fetchall()]
    sql = "SELECT * FROM products WHERE 1=1"
    params = []
    if q:
        sql += " AND (product_code LIKE %s OR name LIKE %s)"
        params += [f"%{q}%", f"%{q}%"]
    if cat:
        sql += " AND category = %s"
        params.append(cat)
    sql += " ORDER BY id"
    cur.execute(sql, params)
    products = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("products.html", products=products, q=q, category=cat, categories=categories)

@app.route("/products/add", methods=["GET", "POST"])
@admin_required
def products_add():
    if request.method == "POST":
        code = request.form.get("product_code", "").strip()
        name = request.form.get("name", "").strip()
        category = request.form.get("category", "").strip()
        try:
            price = float(request.form.get("price", "0"))
            stock = int(request.form.get("stock_quantity", "0"))
        except ValueError:
            flash("Price and Stock must be numbers.")
            return render_template("product_form.html", product=None)
        if not code or not name or not category:
            flash("Product Code, Name and Category are required.")
            return render_template("product_form.html", product=None)
        if price < 0 or stock < 0:
            flash("Price and Stock cannot be negative.")
            return render_template("product_form.html", product=None)
        conn = get_db()
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO products (product_code, name, category, price, stock_quantity, is_active) VALUES (%s, %s, %s, %s, %s, TRUE)",
                        (code, name, category, price, stock))
            conn.commit()
        except Exception as e:
            conn.rollback()
            flash("Product Code already exists. Use a different code.")
            cur.close(); conn.close()
            return render_template("product_form.html", product=None)
        cur.close(); conn.close()
        return redirect(url_for("products_list"))
    return render_template("product_form.html", product=None)

@app.route("/products/<int:pid>/edit", methods=["GET", "POST"])
@admin_required
def products_edit(pid):
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM products WHERE id = %s", (pid,))
    product = cur.fetchone()
    if not product:
        cur.close(); conn.close()
        flash("Product not found.")
        return redirect(url_for("products_list"))
    if request.method == "POST":
        code = request.form.get("product_code", "").strip()
        name = request.form.get("name", "").strip()
        category = request.form.get("category", "").strip()
        try:
            price = float(request.form.get("price", "0"))
            stock = int(request.form.get("stock_quantity", "0"))
        except ValueError:
            flash("Price and Stock must be numbers.")
            cur.close(); conn.close()
            return render_template("product_form.html", product=product)
        if not code or not name or not category or price < 0 or stock < 0:
            flash("Check Code, Name, Category, Price and Stock — none negative, none empty.")
            cur.close(); conn.close()
            return render_template("product_form.html", product=product)
        cur2 = conn.cursor()
        try:
            cur2.execute("UPDATE products SET product_code=%s, name=%s, category=%s, price=%s, stock_quantity=%s WHERE id=%s",
                         (code, name, category, price, stock, pid))
            conn.commit()
        except Exception:
            conn.rollback()
            flash("Product Code already exists. Use a different code.")
            cur2.close(); cur.close(); conn.close()
            return render_template("product_form.html", product=product)
        cur2.close(); cur.close(); conn.close()
        return redirect(url_for("products_list"))
    cur.close(); conn.close()
    return render_template("product_form.html", product=product)

@app.route("/products/<int:pid>/toggle", methods=["POST"])
@admin_required
def products_toggle(pid):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE products SET is_active = NOT is_active WHERE id = %s", (pid,))
    conn.commit()
    cur.close(); conn.close()
    return redirect(url_for("products_list"))

@app.route("/products/<int:pid>/delete", methods=["POST"])
@admin_required
def products_delete(pid):
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT COUNT(*) AS c FROM sales_order_items WHERE product_id = %s", (pid,))
    used = cur.fetchone()["c"]
    if used > 0:
        cur.close(); conn.close()
        flash("Cannot delete — this product is used in orders. Deactivate instead.")
        return redirect(url_for("products_list"))
    cur2 = conn.cursor()
    cur2.execute("DELETE FROM products WHERE id = %s", (pid,))
    conn.commit()
    cur2.close(); cur.close(); conn.close()
    return redirect(url_for("products_list"))

# ---------- Orders (Parts 5, 6, 8) ----------
def calc_totals(items, discount_pct):
    subtotal = sum((Decimal(str(i["qty"])) * Decimal(str(i["rate"])) for i in items), Decimal("0"))
    subtotal = subtotal.quantize(Decimal("0.01"))
    disc = (subtotal * Decimal(str(discount_pct)) / Decimal("100")).quantize(Decimal("0.01"))
    return subtotal, disc, subtotal - disc

def get_order(conn, oid):
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM sales_orders WHERE id = %s", (oid,))
    order = cur.fetchone()
    cur.close()
    return order

@app.route("/orders")
@login_required
def orders_list():
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    if session.get("role") == "Admin":
        cur.execute("""SELECT o.*, c.name AS customer_name, u.name AS created_by_name
                       FROM sales_orders o JOIN customers c ON c.id=o.customer_id
                       JOIN users u ON u.id=o.created_by ORDER BY o.id DESC""")
    else:
        cur.execute("""SELECT o.*, c.name AS customer_name, u.name AS created_by_name
                       FROM sales_orders o JOIN customers c ON c.id=o.customer_id
                       JOIN users u ON u.id=o.created_by
                       WHERE o.created_by = %s ORDER BY o.id DESC""", (session["user_id"],))
    orders = cur.fetchall()
    cur.close(); conn.close()
    return render_template("orders.html", orders=orders)

@app.route("/orders/add", methods=["GET", "POST"])
@login_required
def orders_add():
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM customers WHERE is_active = TRUE ORDER BY name")
    customers = cur.fetchall()
    cur.execute("SELECT * FROM products WHERE is_active = TRUE ORDER BY name")
    products = cur.fetchall()
    if request.method == "POST":
        customer_id = request.form.get("customer_id")
        try:
            discount = Decimal(request.form.get("discount_percentage", "0"))
        except Exception:
            discount = Decimal("-1")
        pids = request.form.getlist("product_id")
        qtys = request.form.getlist("quantity")
        if not customer_id:
            flash("Choose a customer."); cur.close(); conn.close()
            return render_template("order_form.html", customers=customers, products=products)
        if discount < 0 or discount > 20:
            flash("Discount must be 0 to 20%."); cur.close(); conn.close()
            return render_template("order_form.html", customers=customers, products=products)
        if len(pids) != len(set(pids)) or not pids:
            flash("Add at least 1 item, and no duplicate product in one order."); cur.close(); conn.close()
            return render_template("order_form.html", customers=customers, products=products)
        items = []
        for pid, q in zip(pids, qtys):
            try:
                qty = int(q)
                if qty <= 0: raise ValueError()
            except ValueError:
                flash("Quantity must be a whole number above 0."); cur.close(); conn.close()
                return render_template("order_form.html", customers=customers, products=products)
            cur.execute("SELECT * FROM products WHERE id = %s AND is_active = TRUE", (pid,))
            prod = cur.fetchone()
            if not prod:
                flash("A selected product is not available."); cur.close(); conn.close()
                return render_template("order_form.html", customers=customers, products=products)
            rate = Decimal(str(prod["price"]))
            items.append({"product_id": int(pid), "qty": qty, "rate": rate,
                          "amount": (Decimal(qty) * rate).quantize(Decimal("0.01"))})
        subtotal, disc_amt, grand = calc_totals(items, discount)
        cur2 = conn.cursor()
        cur2.execute("""INSERT INTO sales_orders
            (order_number, customer_id, order_date, status, discount_percentage,
             subtotal, discount_amount, grand_total, created_by)
            VALUES ('TEMP', %s, %s, 'Draft', %s, %s, %s, %s, %s)""",
            (customer_id, date.today(), discount, subtotal, disc_amt, grand, session["user_id"]))
        oid = cur2.lastrowid
        cur2.execute("UPDATE sales_orders SET order_number = %s WHERE id = %s", (f"SO-{oid:05d}", oid))
        for it in items:
            cur2.execute("INSERT INTO sales_order_items (sales_order_id, product_id, quantity, rate, amount) VALUES (%s, %s, %s, %s, %s)",
                         (oid, it["product_id"], it["qty"], it["rate"], it["amount"]))
        conn.commit()
        cur2.close(); cur.close(); conn.close()
        return redirect(url_for("orders_detail", oid=oid))
    cur.close(); conn.close()
    return render_template("order_form.html", customers=customers, products=products)

@app.route("/orders/<int:oid>")
@login_required
def orders_detail(oid):
    conn = get_db()
    order = get_order(conn, oid)
    if not order:
        conn.close(); flash("Order not found."); return redirect(url_for("orders_list"))
    if session.get("role") != "Admin" and order["created_by"] != session["user_id"]:
        conn.close(); flash("You cannot view another user's order."); return redirect(url_for("orders_list"))
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT name FROM customers WHERE id = %s", (order["customer_id"],))
    customer = cur.fetchone()
    cur.execute("""SELECT i.*, p.product_code, p.name AS product_name
                   FROM sales_order_items i JOIN products p ON p.id=i.product_id
                   WHERE i.sales_order_id = %s""", (oid,))
    items = cur.fetchall()
    cur.execute("SELECT * FROM stock_movements WHERE related_order_id = %s ORDER BY id", (oid,))
    movements = cur.fetchall()
    cur.close(); conn.close()
    return render_template("order_detail.html", order=order, customer=customer, items=items, movements=movements)

@app.route("/orders/<int:oid>/confirm", methods=["POST"])
@login_required
def orders_confirm(oid):
    conn = get_db()
    order = get_order(conn, oid)
    if not order:
        conn.close(); flash("Order not found."); return redirect(url_for("orders_list"))
    if session.get("role") != "Admin" and order["created_by"] != session["user_id"]:
        conn.close(); flash("You cannot confirm another user's order."); return redirect(url_for("orders_list"))
    if order["status"] != "Draft":
        conn.close(); flash(f"Only a Draft order can be confirmed. This one is {order['status']}.")
        return redirect(url_for("orders_detail", oid=oid))
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM sales_order_items WHERE sales_order_id = %s", (oid,))
        items = cur.fetchall()
        for it in items:
            cur.execute("SELECT stock_quantity FROM products WHERE id = %s FOR UPDATE", (it["product_id"],))
            prod = cur.fetchone()
            if prod["stock_quantity"] < it["quantity"]:
                raise Exception(f"Insufficient stock for product id {it['product_id']}: need {it['quantity']}, have {prod['stock_quantity']}.")
        for it in items:
            cur.execute("UPDATE products SET stock_quantity = stock_quantity - %s WHERE id = %s", (it["quantity"], it["product_id"]))
            cur.execute("""INSERT INTO stock_movements (product_id, movement_type, quantity_change, related_order_id, reason, created_by)
                           VALUES (%s, 'SALE', %s, %s, %s, %s)""",
                        (it["product_id"], -it["quantity"], oid, f"Order {order['order_number']} confirmed", session["user_id"]))
        cur.execute("UPDATE sales_orders SET status = 'Confirmed' WHERE id = %s", (oid,))
        conn.commit()
        flash("Order confirmed. Stock deducted.")
    except Exception as e:
        conn.rollback()
        flash(str(e))
    finally:
        conn.close()
    return redirect(url_for("orders_detail", oid=oid))

@app.route("/orders/<int:oid>/cancel", methods=["POST"])
@login_required
def orders_cancel(oid):
    conn = get_db()
    order = get_order(conn, oid)
    if not order:
        conn.close(); flash("Order not found."); return redirect(url_for("orders_list"))
    if session.get("role") != "Admin" and order["created_by"] != session["user_id"]:
        conn.close(); flash("You cannot cancel another user's order."); return redirect(url_for("orders_list"))
    if order["status"] == "Cancelled":
        conn.close(); flash("Order is already Cancelled. Stock was already restored once.")
        return redirect(url_for("orders_detail", oid=oid))
    try:
        cur = conn.cursor(dictionary=True)
        if order["status"] == "Confirmed":
            cur.execute("SELECT * FROM sales_order_items WHERE sales_order_id = %s", (oid,))
            items = cur.fetchall()
            for it in items:
                cur.execute("UPDATE products SET stock_quantity = stock_quantity + %s WHERE id = %s", (it["quantity"], it["product_id"]))
                cur.execute("""INSERT INTO stock_movements (product_id, movement_type, quantity_change, related_order_id, reason, created_by)
                               VALUES (%s, 'SALE_REVERSAL', %s, %s, %s, %s)""",
                            (it["product_id"], it["quantity"], oid, f"Order {order['order_number']} cancelled", session["user_id"]))
        cur.execute("UPDATE sales_orders SET status = 'Cancelled' WHERE id = %s", (oid,))
        conn.commit()
        flash("Order cancelled.")
    except Exception as e:
        conn.rollback(); flash(str(e))
    finally:
        conn.close()
    return redirect(url_for("orders_detail", oid=oid))

@app.route("/products/<int:pid>/adjust", methods=["POST"])
@admin_required
def products_adjust(pid):
    reason = request.form.get("reason", "").strip()
    try:
        change = int(request.form.get("quantity_change", "0"))
    except ValueError:
        flash("Quantity change must be a whole number."); return redirect(url_for("products_list"))
    if not reason:
        flash("Reason is mandatory for a stock adjustment."); return redirect(url_for("products_list"))
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT stock_quantity FROM products WHERE id = %s FOR UPDATE", (pid,))
    prod = cur.fetchone()
    if not prod:
        cur.close(); conn.close(); flash("Product not found."); return redirect(url_for("products_list"))
    if prod["stock_quantity"] + change < 0:
        cur.close(); conn.close(); flash("Adjustment would make stock negative."); return redirect(url_for("products_list"))
    cur.execute("UPDATE products SET stock_quantity = stock_quantity + %s WHERE id = %s", (change, pid))
    cur.execute("""INSERT INTO stock_movements (product_id, movement_type, quantity_change, related_order_id, reason, created_by)
                   VALUES (%s, 'ADJUSTMENT', %s, NULL, %s, %s)""", (pid, change, reason, session["user_id"]))
    conn.commit(); cur.close(); conn.close()
    flash("Stock adjusted.")
    return redirect(url_for("products_list"))

# ---------- REST API (Part 8) ----------
@app.route("/api/products")
@login_required
def api_products():
    q = request.args.get("q", "").strip()
    try:
        page = max(int(request.args.get("page", "1")), 1)
    except ValueError:
        page = 1
    per_page = 10
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    if q:
        like = f"%{q}%"
        cur.execute("SELECT COUNT(*) AS c FROM products WHERE is_active=TRUE AND (product_code LIKE %s OR name LIKE %s)", (like, like))
        total = cur.fetchone()["c"]
        cur.execute("SELECT id, product_code, name, category, price, stock_quantity FROM products WHERE is_active=TRUE AND (product_code LIKE %s OR name LIKE %s) ORDER BY id LIMIT %s OFFSET %s",
                    (like, like, per_page, (page-1)*per_page))
    else:
        cur.execute("SELECT COUNT(*) AS c FROM products WHERE is_active=TRUE")
        total = cur.fetchone()["c"]
        cur.execute("SELECT id, product_code, name, category, price, stock_quantity FROM products WHERE is_active=TRUE ORDER BY id LIMIT %s OFFSET %s",
                    (per_page, (page-1)*per_page))
    rows = cur.fetchall()
    cur.close(); conn.close()
    for r in rows:
        r["price"] = float(r["price"])
    return {"page": page, "per_page": per_page, "total": total, "products": rows}

# ---------- Reports (Part 9) ----------
@app.route("/reports")
@login_required
def reports():
    start = request.args.get("start", "")
    end = request.args.get("end", "")
    try:
        threshold = int(request.args.get("threshold", "10"))
    except ValueError:
        threshold = 10
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    # Customer Sales Summary — Confirmed only, include customers with zero orders
    if start and end:
        cur.execute("""SELECT c.id, c.name, c.email,
            COUNT(DISTINCT o.id) AS order_count,
            COALESCE(SUM(o.grand_total), 0) AS total_sales
            FROM customers c
            LEFT JOIN sales_orders o ON o.customer_id = c.id
                AND o.status = 'Confirmed' AND o.order_date BETWEEN %s AND %s
            GROUP BY c.id, c.name, c.email ORDER BY total_sales DESC""", (start, end))
    else:
        cur.execute("""SELECT c.id, c.name, c.email,
            COUNT(DISTINCT o.id) AS order_count,
            COALESCE(SUM(o.grand_total), 0) AS total_sales
            FROM customers c
            LEFT JOIN sales_orders o ON o.customer_id = c.id AND o.status = 'Confirmed'
            GROUP BY c.id, c.name, c.email ORDER BY total_sales DESC""")
    customer_sales = cur.fetchall()
    # Product Sales Summary — Confirmed only, quantity sold per product
    cur.execute("""SELECT p.product_code, p.name,
            COALESCE(SUM(i.quantity), 0) AS qty_sold,
            COALESCE(SUM(i.amount), 0) AS total_amount
            FROM products p
            LEFT JOIN sales_order_items i ON i.product_id = p.id
            LEFT JOIN sales_orders o ON o.id = i.sales_order_id AND o.status = 'Confirmed'
            GROUP BY p.id, p.product_code, p.name ORDER BY qty_sold DESC""")
    product_sales = cur.fetchall()
    # Low Stock Report — user-entered threshold
    cur.execute("SELECT product_code, name, stock_quantity FROM products WHERE stock_quantity < %s ORDER BY stock_quantity",
                (threshold,))
    low_stock = cur.fetchall()
    # Stock Movement History — newest first
    cur.execute("""SELECT m.*, p.product_code, p.name AS product_name, u.name AS created_by_name
                   FROM stock_movements m
                   JOIN products p ON p.id = m.product_id
                   JOIN users u ON u.id = m.created_by
                   ORDER BY m.id DESC LIMIT 100""")
    movements = cur.fetchall()
    cur.close(); conn.close()
    return render_template("reports.html", customer_sales=customer_sales,
                           product_sales=product_sales, low_stock=low_stock,
                           movements=movements, start=start, end=end, threshold=threshold)

# ---------- CSV Import (Part 10) ----------
@app.route("/products/import", methods=["GET", "POST"])
@admin_required
def products_import():
    errors = []
    imported = None
    if request.method == "POST":
        file = request.files.get("file")
        if not file or not file.filename.endswith(".csv"):
            flash("Upload a .csv file.")
            return render_template("import.html", errors=errors, imported=imported)
        try:
            text = file.stream.read().decode("utf-8")
        except Exception:
            flash("Could not read the file as UTF-8 text.")
            return render_template("import.html", errors=errors, imported=imported)
        reader = csv.DictReader(io.StringIO(text))
        expected = ["product_code", "product_name", "category", "price", "stock_quantity", "status"]
        if reader.fieldnames != expected:
            flash(f"Wrong columns. Expected: {', '.join(expected)}")
            return render_template("import.html", errors=errors, imported=imported)
        rows = list(reader)
        # Validate ALL rows first — nothing is inserted yet
        seen_codes = set()
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT product_code FROM products")
        existing = {r["product_code"] for r in cur.fetchall()}
        for i, row in enumerate(rows, start=2):  # row 1 is the header
            code = (row.get("product_code") or "").strip()
            name = (row.get("product_name") or "").strip()
            category = (row.get("category") or "").strip()
            status = (row.get("status") or "").strip()
            try:
                price = float(row.get("price", ""))
                stock = int(row.get("stock_quantity", ""))
            except (ValueError, TypeError):
                errors.append(f"Row {i}: price/stock must be numbers.")
                continue
            if not code or not name or not category:
                errors.append(f"Row {i}: product_code, product_name and category are required.")
            if code in seen_codes:
                errors.append(f"Row {i}: duplicate product_code '{code}' inside this file.")
            if code in existing:
                errors.append(f"Row {i}: product_code '{code}' already exists in the database.")
            if price < 0:
                errors.append(f"Row {i}: price cannot be negative.")
            if stock < 0:
                errors.append(f"Row {i}: stock_quantity cannot be negative.")
            if status not in ("Active", "Inactive"):
                errors.append(f"Row {i}: status must be Active or Inactive.")
            seen_codes.add(code)
        if errors:
            cur.close(); conn.close()
            return render_template("import.html", errors=errors, imported=None)
        # All rows valid — insert everything in one transaction
        try:
            cur2 = conn.cursor()
            for row in rows:
                price = float(row["price"]); stock = int(row["stock_quantity"])
                active = row["status"].strip() == "Active"
                cur2.execute("INSERT INTO products (product_code, name, category, price, stock_quantity, is_active) VALUES (%s, %s, %s, %s, %s, %s)",
                             (row["product_code"].strip(), row["product_name"].strip(), row["category"].strip(), price, stock, active))
                pid = cur2.lastrowid
                cur2.execute("""INSERT INTO stock_movements (product_id, movement_type, quantity_change, related_order_id, reason, created_by)
                                VALUES (%s, 'IMPORT', %s, NULL, %s, %s)""",
                             (pid, stock, "Opening stock from CSV import", session["user_id"]))
            conn.commit()
            imported = len(rows)
        except Exception as e:
            conn.rollback()
            errors.append(f"Import failed: {e}")
        finally:
            cur.close(); conn.close()
    return render_template("import.html", errors=errors, imported=imported)

# ---------- REST API — Orders (Part 8, continued) ----------
@app.route("/api/orders", methods=["POST"])
@login_required
def api_create_order():
    data = request.get_json(silent=True) or {}
    customer_id = data.get("customer_id")
    items_in = data.get("items") or []
    try:
        discount = Decimal(str(data.get("discount_percentage", "0")))
    except Exception:
        return jsonify({"error": "discount_percentage must be a number."}), 400
    if not customer_id:
        return jsonify({"error": "customer_id is required."}), 400
    if discount < 0 or discount > 20:
        return jsonify({"error": "Discount must be 0 to 20%."}), 400
    if not items_in:
        return jsonify({"error": "At least 1 item is required."}), 400
    pids = [i.get("product_id") for i in items_in]
    if len(pids) != len(set(pids)):
        return jsonify({"error": "Duplicate product in one order is not allowed."}), 400
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM customers WHERE id = %s AND is_active = TRUE", (customer_id,))
    if not cur.fetchone():
        cur.close(); conn.close()
        return jsonify({"error": "Customer not found or inactive."}), 400
    items = []
    for it in items_in:
        try:
            qty = int(it.get("quantity"))
            if qty <= 0: raise ValueError()
        except (ValueError, TypeError):
            cur.close(); conn.close()
            return jsonify({"error": "Quantity must be a whole number above 0."}), 400
        cur.execute("SELECT * FROM products WHERE id = %s AND is_active = TRUE", (it.get("product_id"),))
        prod = cur.fetchone()
        if not prod:
            cur.close(); conn.close()
            return jsonify({"error": f"Product {it.get('product_id')} not found or inactive."}), 400
        rate = Decimal(str(prod["price"]))
        items.append({"product_id": int(it["product_id"]), "qty": qty, "rate": rate,
                      "amount": (Decimal(qty) * rate).quantize(Decimal("0.01"))})
    subtotal, disc_amt, grand = calc_totals(items, discount)
    cur2 = conn.cursor()
    cur2.execute("""INSERT INTO sales_orders
        (order_number, customer_id, order_date, status, discount_percentage,
         subtotal, discount_amount, grand_total, created_by)
        VALUES ('TEMP', %s, %s, 'Draft', %s, %s, %s, %s, %s)""",
        (customer_id, date.today(), discount, subtotal, disc_amt, grand, session["user_id"]))
    oid = cur2.lastrowid
    cur2.execute("UPDATE sales_orders SET order_number = %s WHERE id = %s", (f"SO-{oid:05d}", oid))
    for it in items:
        cur2.execute("INSERT INTO sales_order_items (sales_order_id, product_id, quantity, rate, amount) VALUES (%s, %s, %s, %s, %s)",
                     (oid, it["product_id"], it["qty"], it["rate"], it["amount"]))
    conn.commit()
    cur2.close(); cur.close(); conn.close()
    return jsonify({"order_id": oid, "order_number": f"SO-{oid:05d}", "status": "Draft",
                    "subtotal": float(subtotal), "discount_amount": float(disc_amt),
                    "grand_total": float(grand)}), 201

@app.route("/api/orders/<int:oid>")
@login_required
def api_get_order(oid):
    conn = get_db()
    order = get_order(conn, oid)
    if not order:
        conn.close(); return jsonify({"error": "Order not found."}), 404
    if session.get("role") != "Admin" and order["created_by"] != session["user_id"]:
        conn.close(); return jsonify({"error": "You cannot view another user's order."}), 403
    cur = conn.cursor(dictionary=True)
    cur.execute("""SELECT i.product_id, p.product_code, p.name AS product_name,
                   i.quantity, i.rate, i.amount
                   FROM sales_order_items i JOIN products p ON p.id = i.product_id
                   WHERE i.sales_order_id = %s""", (oid,))
    items = cur.fetchall()
    cur.close(); conn.close()
    for k in ("subtotal", "discount_amount", "grand_total", "discount_percentage"):
        order[k] = float(order[k])
    for i in items:
        i["rate"] = float(i["rate"]); i["amount"] = float(i["amount"])
    order["order_date"] = str(order["order_date"])
    order["items"] = items
    return jsonify(order), 200

@app.route("/api/orders/<int:oid>/confirm", methods=["POST"])
@login_required
def api_confirm_order(oid):
    conn = get_db()
    order = get_order(conn, oid)
    if not order:
        conn.close(); return jsonify({"error": "Order not found."}), 404
    if session.get("role") != "Admin" and order["created_by"] != session["user_id"]:
        conn.close(); return jsonify({"error": "You cannot confirm another user's order."}), 403
    if order["status"] != "Draft":
        conn.close(); return jsonify({"error": f"Only a Draft order can be confirmed. This one is {order['status']}."}), 400
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM sales_order_items WHERE sales_order_id = %s", (oid,))
        items = cur.fetchall()
        for it in items:
            cur.execute("SELECT stock_quantity FROM products WHERE id = %s FOR UPDATE", (it["product_id"],))
            prod = cur.fetchone()
            if prod["stock_quantity"] < it["quantity"]:
                raise Exception(f"Insufficient stock for product id {it['product_id']}: need {it['quantity']}, have {prod['stock_quantity']}.")
        for it in items:
            cur.execute("UPDATE products SET stock_quantity = stock_quantity - %s WHERE id = %s", (it["quantity"], it["product_id"]))
            cur.execute("""INSERT INTO stock_movements (product_id, movement_type, quantity_change, related_order_id, reason, created_by)
                           VALUES (%s, 'SALE', %s, %s, %s, %s)""",
                        (it["product_id"], -it["quantity"], oid, f"Order {order['order_number']} confirmed", session["user_id"]))
        cur.execute("UPDATE sales_orders SET status = 'Confirmed' WHERE id = %s", (oid,))
        conn.commit()
    except Exception as e:
        conn.rollback(); conn.close()
        return jsonify({"error": str(e)}), 400
    conn.close()
    return jsonify({"order_id": oid, "order_number": order["order_number"], "status": "Confirmed"}), 200

@app.route("/api/orders/<int:oid>/cancel", methods=["POST"])
@login_required
def api_cancel_order(oid):
    conn = get_db()
    order = get_order(conn, oid)
    if not order:
        conn.close(); return jsonify({"error": "Order not found."}), 404
    if session.get("role") != "Admin" and order["created_by"] != session["user_id"]:
        conn.close(); return jsonify({"error": "You cannot cancel another user's order."}), 403
    if order["status"] == "Cancelled":
        conn.close(); return jsonify({"error": "Order is already Cancelled."}), 400
    try:
        cur = conn.cursor(dictionary=True)
        if order["status"] == "Confirmed":
            cur.execute("SELECT * FROM sales_order_items WHERE sales_order_id = %s", (oid,))
            items = cur.fetchall()
            for it in items:
                cur.execute("UPDATE products SET stock_quantity = stock_quantity + %s WHERE id = %s", (it["quantity"], it["product_id"]))
                cur.execute("""INSERT INTO stock_movements (product_id, movement_type, quantity_change, related_order_id, reason, created_by)
                               VALUES (%s, 'SALE_REVERSAL', %s, %s, %s, %s)""",
                            (it["product_id"], it["quantity"], oid, f"Order {order['order_number']} cancelled", session["user_id"]))
        cur.execute("UPDATE sales_orders SET status = 'Cancelled' WHERE id = %s", (oid,))
        conn.commit()
    except Exception as e:
        conn.rollback(); conn.close()
        return jsonify({"error": str(e)}), 400
    conn.close()
    return jsonify({"order_id": oid, "order_number": order["order_number"], "status": "Cancelled"}), 200

if __name__ == "__main__":
    app.run(debug=True)
