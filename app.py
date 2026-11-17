from flask import Flask, request, redirect, session, render_template_string
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "greenleaf123"

def get_db():
    conn = sqlite3.connect("greenleaf.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""CREATE TABLE IF NOT EXISTS products
        (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, category TEXT, price REAL, stock INTEGER, expiry TEXT)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS sales
        (id INTEGER PRIMARY KEY AUTOINCREMENT, product_name TEXT, price REAL, qty INTEGER, total REAL, date TEXT)""")
    conn.commit()
    conn.close()

init_db()

STYLE = """
<style>
body{font-family:Arial,sans-serif;background:#f0f7f0;margin:0;padding:0}
.header{background:#2e7d32;color:white;padding:18px 30px;display:flex;justify-content:space-between;align-items:center}
.header a{color:white;text-decoration:none;margin-left:18px;font-weight:bold}
.container{max-width:900px;margin:25px auto;background:white;padding:25px;border-radius:12px;box-shadow:0 4px 12px rgba(0,0,0,0.1)}
h2{margin:0} h3{color:#2e7d32}
table{width:100%;border-collapse:collapse;margin-top:15px}
th{background:#2e7d32;color:white;padding:10px}
td{padding:10px;border-bottom:1px solid #ddd;text-align:center}
.btn{background:#2e7d32;color:white;padding:9px 18px;border:none;border-radius:6px;cursor:pointer;font-size:15px;text-decoration:none;display:inline-block}
.btn-red{background:#d32f2f} .btn-blue{background:#1976d2}
input,select{padding:8px;width:280px;border:1px solid #ccc;border-radius:6px;margin:4px 0}
.search-box{display:flex;gap:10px;margin:15px 0}
.badge{padding:4px 10px;border-radius:12px;color:white;font-size:12px}
.ok{background:#2e7d32} .low{background:#ff9800} .exp{background:#d32f2f}
</style>
"""

BASE = STYLE + """
<div class="header"><h2>🌿 GreenLeaf</h2><div>
<a href="/products">Products</a><a href="/billing">Billing</a><a href="/bills">Bill History</a><a href="/logout">Logout</a>
</div></div><div class="container">{{body}}</div>
"""

def page(body):
    return render_template_string(BASE.replace("{{body}}", body))

@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        if request.form["username"]=="admin" and request.form["password"]=="admin123":
            session["user"]="admin"
            return redirect("/products")
        return "Invalid Login! <a href='/'>Go Back</a>"
    return STYLE + """<div class="container" style="max-width:400px;margin-top:80px;text-align:center">
    <h2 style="color:#2e7d32;font-size:32px">🌿 GreenLeaf</h2><p>Grocery Store Management</p>
    <form method="post" style="text-align:left">
    Username:<br><input name="username"><br><br>
    Password:<br><input type="password" name="password"><br><br>
    <button class="btn" style="width:100%">Login</button></form>
    <p style="font-size:12px;color:#888">Demo: admin / admin123</p></div>"""

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/products")
def products():
    if "user" not in session: return redirect("/")
    q = request.args.get("q","")
    conn = get_db()
    if q:
        rows = conn.execute("SELECT * FROM products WHERE name LIKE ?", ("%"+q+"%",)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM products").fetchall()
    conn.close()
    html = f"""<h3>Products</h3>
    <a href="/add" class="btn">+ Add New Product</a> <a href="/billing" class="btn btn-blue">Go to Billing</a><br><br>
    <form class="search-box"><input name="q" value="{q}" placeholder="Search product..."> <button class="btn">Search</button></form>
    <table><tr><th>Name</th><th>Category</th><th>Price</th><th>Stock</th><th>Expiry</th><th>Status</th><th>Action</th></tr>"""
    for r in rows:
        if r["stock"]<=5:
            status = "<span class='badge low'>LOW STOCK</span>"
        elif r["expiry"] < datetime.now().strftime("%Y-%m-%d"):
            status = "<span class='badge exp'>EXPIRED</span>"
        else:
            status = "<span class='badge ok'>OK</span>"
        html += f"<tr><td>{r['name']}</td><td>{r['category']}</td><td>Rs. {r['price']}</td><td>{r['stock']}</td><td>{r['expiry']}</td><td>{status}</td><td><a href='/edit/{r['id']}'>Edit</a> | <a href='/delete/{r['id']}' style='color:red'>Delete</a></td></tr>"
    html += "</table>"
    return page(html)

@app.route("/add", methods=["GET","POST"])
def add():
    if "user" not in session: return redirect("/")
    if request.method=="POST":
        conn=get_db()
        conn.execute("INSERT INTO products (name,category,price,stock,expiry) VALUES (?,?,?,?,?)",
            (request.form["name"], request.form["category"], request.form["price"], request.form["stock"], request.form["expiry"]))
        conn.commit(); conn.close()
        return redirect("/products")
    return page("""<h3>Add Product</h3><form method="post">
    Name:<br><input name="name" required><br><br>
    Category:<br><input name="category" placeholder="Dairy / Snacks"><br><br>
    Price:<br><input type="number" step="0.01" name="price" required><br><br>
    Stock:<br><input type="number" name="stock" required><br><br>
    Expiry:<br><input type="date" name="expiry" required><br><br>
    <button class="btn">Save Product</button></form>""")

@app.route("/edit/<int:id>", methods=["GET","POST"])
def edit(id):
    if "user" not in session: return redirect("/")
    conn=get_db()
    p=conn.execute("SELECT * FROM products WHERE id=?", (id,)).fetchone()
    if request.method=="POST":
        conn.execute("UPDATE products SET name=?,category=?,price=?,stock=?,expiry=? WHERE id=?",
            (request.form["name"], request.form["category"], request.form["price"], request.form["stock"], request.form["expiry"], id))
        conn.commit(); conn.close()
        return redirect("/products")
    conn.close()
    return page(f"""<h3>Edit Product</h3><form method="post">
    Name:<br><input name="name" value="{p['name']}"><br><br>
    Category:<br><input name="category" value="{p['category']}"><br><br>
    Price:<br><input name="price" value="{p['price']}"><br><br>
    Stock:<br><input name="stock" value="{p['stock']}"><br><br>
    Expiry:<br><input type="date" name="expiry" value="{p['expiry']}"><br><br>
    <button class="btn">Update Product</button></form>""")

@app.route("/delete/<int:id>")
def delete(id):
    if "user" not in session: return redirect("/")
    conn=get_db(); conn.execute("DELETE FROM products WHERE id=?", (id,)); conn.commit(); conn.close()
    return redirect("/products")

@app.route("/billing", methods=["GET","POST"])
def billing():
    if "user" not in session: return redirect("/")
    conn=get_db()
    products = conn.execute("SELECT * FROM products WHERE stock>0").fetchall()
    msg=""
    if request.method=="POST":
        pid = request.form["product"]
        qty = int(request.form["qty"])
        p = conn.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()
        if p and qty <= p["stock"]:
            total = p["price"]*qty
            conn.execute("UPDATE products SET stock=stock-? WHERE id=?", (qty, pid))
            conn.execute("INSERT INTO sales (product_name, price, qty, total, date) VALUES (?,?,?,?,?)",
                (p["name"], p["price"], qty, total, datetime.now().strftime("%Y-%m-%d %H:%M")))
            conn.commit()
            msg = f"<div style='background:#e8f5e9;padding:15px;border-radius:8px'><b>Bill Created Successfully!</b><br>{p['name']} x {qty} = Rs. {total}<br><a href='/bills'>View Bill History</a></div><br>"
        else:
            msg = "<div style='background:#ffebee;padding:15px;border-radius:8px;color:red'><b>Insufficient Stock!</b></div><br>"
    conn.close()
    opts = "".join([f"<option value='{p['id']}'>{p['name']} - Rs.{p['price']} (Stock: {p['stock']})</option>" for p in products])
    return page(f"""{msg}<h3>Billing - Create New Bill</h3>
    <form method="post">Product:<br><select name="product">{opts}</select><br><br>
    Quantity:<br><input type="number" name="qty" value="1" min="1" required><br><br>
    <button class="btn" style="font-size:18px;padding:12px 30px">Create Bill</button></form>""")

@app.route("/bills")
def bills():
    if "user" not in session: return redirect("/")
    conn=get_db()
    rows=conn.execute("SELECT * FROM sales ORDER BY id DESC").fetchall()
    total_sum = conn.execute("SELECT SUM(total) as s FROM sales").fetchone()["s"] or 0
    conn.close()
    html=f"<h3>Bill History</h3><div style='background:#e8f5e9;padding:15px;border-radius:8px'><b>Total Sales: Rs. {total_sum}</b></div><table><tr><th>ID</th><th>Product</th><th>Price</th><th>Qty</th><th>Total</th><th>Date</th></tr>"
    for r in rows:
        html+=f"<tr><td>{r['id']}</td><td>{r['product_name']}</td><td>Rs. {r['price']}</td><td>{r['qty']}</td><td><b>Rs. {r['total']}</b></td><td>{r['date']}</td></tr>"
    html+="</table>"
    return page(html)

if __name__=="__main__":
    app.run(debug=True)