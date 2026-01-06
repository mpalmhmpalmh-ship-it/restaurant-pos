from flask import Flask, redirect

app = Flask(__name__)

@app.route("/")
def home():
    return "POS is running ✅"

from flask import redirect

@app.route("/")
def home():
    return redirect("/pos")
from flask import Flask, request, redirect
import sqlite3
from datetime import datetime


# ---------------- DB ----------------
def db():
    return sqlite3.connect("restaurant.db")

def init_db():
    con = db()
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS orders(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer TEXT,
        table_no TEXT,
        items TEXT,
        total INTEGER,
        status TEXT
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS invoices(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer TEXT,
        table_no TEXT,
        items TEXT,
        total INTEGER,
        date TEXT
    )""")

    con.commit(); con.close()

init_db()

# ---------------- MENU ----------------
MENU = {
    "چلوکباب":150000,
    "چلوجوجه":120000,
    "قورمه سبزی":110000,
    "قیمه":110000,
    "چلو میکس":220000
}

# ---------------- STYLE ----------------
STYLE = """
<link rel="stylesheet"
 href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
<style>
body{margin:0;font-family:tahoma;direction:rtl;background:#eee7dc}
header{
background:#0f3d3e;color:#f3d9a4;
padding:16px;font-size:20px;
display:flex;justify-content:space-between
}
.container{max-width:1000px;margin:auto;padding:25px}

.card{
background:white;border-radius:18px;
padding:20px;margin-bottom:18px;
box-shadow:0 8px 22px rgba(0,0,0,.18)
}

.btn{
border:none;border-radius:14px;
padding:12px 16px;
font-size:15px;cursor:pointer;
text-decoration:none;display:inline-block
}
.primary{background:#0f3d3e;color:white}
.warn{background:#8b5e3c;color:white}
.back{background:#6b7280;color:white}
.full{width:100%;text-align:center}

.menu-item{
display:flex;justify-content:space-between;
background:#f2eadf;padding:14px;
border-radius:14px;margin-bottom:6px
}
input{
width:80px;padding:8px;
border-radius:10px;border:1px solid #ccc
}

table{
width:100%;border-collapse:collapse;font-size:15px
}
th,td{
padding:10px;border-bottom:1px solid #ddd
}
th{background:#f1eadf}
.total{
font-size:20px;color:#8b5e3c;font-weight:bold
}

.navbar{
position:fixed;bottom:0;left:0;right:0;
background:#102c2d;
display:flex;gap:10px;
padding:10px;justify-content:center
}
.navbar a{
color:white;text-decoration:none;
padding:10px 18px;border-radius:12px;
background:#0f3d3e;font-size:14px
}

@media print{
body{background:white}
header,.navbar,.btn{display:none}
.receipt{
width:80mm;
font-size:14px;
}
}
</style>
"""

def page(title, body):
    nav = """
    <div class='navbar'>
      <a href='/'><i class='fa-solid fa-house'></i> منوی اصلی</a>
      <a href='javascript:history.back()'><i class='fa-solid fa-arrow-right'></i> بازگشت</a>
    </div>
    """
    return f"""
    <html><head><meta charset='utf-8'>{STYLE}</head>
    <body>
    <header>
      <b>🍽 رستوران میرزا</b>
      <span>{title}</span>
    </header>
    <div class='container'>{body}</div>
    {nav}
    </body></html>
    """

# ---------------- DASHBOARD ----------------
@app.route("/")
def home():
    return page("داشبورد", """
    <div class='card'><a class='btn primary full' href='/waiter'>
    👤 پنل گارسون</a></div>
    <div class='card'><a class='btn primary full' href='/kitchen'>
    🍳 پنل آشپزخانه</a></div>
    <div class='card'><a class='btn primary full' href='/cashier'>
    💳 پنل صندوق</a></div>
    """)

# ---------------- WAITER ----------------
@app.route("/waiter")
def waiter():
    html=""
    for n,p in MENU.items():
        html+=f"""
        <div class='menu-item'>
        {n} ({p} تومان)
        <input type='number' min='0' value='0' name='{n}'>
        </div>"""
    return page("ثبت سفارش", f"""
    <form method='post' action='/save' class='card'>
      <input name='customer' placeholder='نام مشتری' required>
      <input name='table' placeholder='شماره میز'>
      {html}
      <button class='btn primary full'>ثبت سفارش</button>
    </form>
    """)

@app.route("/save",methods=["POST"])
def save():
    items=[]; total=0
    for n,p in MENU.items():
        q=int(request.form[n])
        if q>0:
            items.append(f"{n}×{q}")
            total+=p*q
    con=db()
    con.execute("INSERT INTO orders VALUES(NULL,?,?,?,?,?)",
    (request.form["customer"],request.form["table"],
     "، ".join(items), total,"kitchen"))
    con.commit(); con.close()
    return redirect("/")

# ---------------- KITCHEN ----------------
@app.route("/kitchen")
def kitchen():
    con=db()
    rows=con.execute("SELECT * FROM orders WHERE status='kitchen'").fetchall()
    con.close()
    body="<div class='card'><table><tr><th>میز</th><th>سفارش</th><th></th></tr>"
    for r in rows:
        body+=f"""
        <tr>
          <td>{r[2]}</td>
          <td>{r[3]}</td>
          <td><a class='btn warn' href='/ready/{r[0]}'>✅</a></td>
        </tr>"""
    body+="</table></div>"
    return page("آشپزخانه", body)

@app.route("/ready/<int:i>")
def ready(i):
    con=db()
    con.execute("UPDATE orders SET status='cashier' WHERE id=?", (i,))
    con.commit(); con.close()
    return redirect("/kitchen")

# ---------------- CASHIER ----------------
@app.route("/cashier")
def cashier():
    con=db()
    orders=con.execute("SELECT * FROM orders WHERE status='cashier'").fetchall()
    invoices=con.execute("SELECT * FROM invoices ORDER BY id DESC").fetchall()
    total=sum(i[4] for i in invoices)
    con.close()

    body="<h3>🧾 سفارش‌های آماده</h3>"
    for r in orders:
        body+=f"""
        <div class='card'>
        <b>{r[1]}</b> | میز {r[2]}<br>{r[3]}
        <div class='total'>{r[4]} تومان</div>
        <a class='btn primary full' href='/pay/{r[0]}'>پرداخت و چاپ</a>
        </div>"""

    body+=f"""
    <div class='card'>
    <h3>📊 جمع فروش</h3>
    <div class='total'>{total} تومان</div>
    </div>

    <div class='card'>
    <h3>🗂 فاکتورهای قبلی</h3>
    <table>
      <tr><th>#</th><th>مبلغ</th><th>تاریخ</th><th></th></tr>
    """
    for i in invoices:
        body+=f"""
        <tr>
          <td>{i[0]}</td>
          <td>{i[4]}</td>
          <td>{i[5]}</td>
          <td><a href='/print/{i[0]}'>🖨️</a></td>
        </tr>"""
    body+="</table></div>"

    return page("صندوق", body)

@app.route("/pay/<int:i>")
def pay(i):
    con=db();cur=con.cursor()
    r=cur.execute("SELECT customer,table_no,items,total FROM orders WHERE id=?", (i,)).fetchone()
    cur.execute("INSERT INTO invoices VALUES(NULL,?,?,?,?,?)",
    (r[0],r[1],r[2],r[3],datetime.now().strftime("%Y/%m/%d %H:%M")))
    cur.execute("DELETE FROM orders WHERE id=?", (i,))
    con.commit(); con.close()
    return redirect("/cashier")

@app.route("/print/<int:i>")
def print_inv(i):
    con=db()
    r=con.execute("SELECT * FROM invoices WHERE id=?", (i,)).fetchone()
    con.close()
    return f"""
    <html><head>{STYLE}</head>
    <body onload='window.print()'>
    <div class='receipt'>
    <h3>رستوران میرزا</h3>
    فاکتور شماره {r[0]}<hr>
    مشتری: {r[1]}<br>
    میز: {r[2]}<br><br>
    {r[3]}<hr>
    <b>جمع کل: {r[4]} تومان</b><br><br>
    {r[5]}
    </div>
    </body></html>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)



