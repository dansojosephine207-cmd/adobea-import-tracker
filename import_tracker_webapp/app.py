from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for
import csv, os, io
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "adobea-import-tracker-secret-key-change-me")

DATA_FILE = "data.csv"
FIELDS = ["id", "item_name", "tracking_number", "customer_name", "shipping_fee", "customer_price", "profit", "date_added"]

# Login credentials - change these!
USERNAME = os.environ.get("APP_USERNAME", "adobea")
PASSWORD = os.environ.get("APP_PASSWORD", "import2026")


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    rows = []
    with open(DATA_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Add customer_name field if missing from old data (won't break old rows)
            if "customer_name" not in row or row["customer_name"] is None:
                row["customer_name"] = ""
            rows.append(row)
    return rows


def save_data(rows):
    with open(DATA_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if username == USERNAME and password == PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("index"))
        else:
            error = "Incorrect username or password"
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("login"))


@app.route("/")
@login_required
def index():
    return render_template("index.html")


@app.route("/api/items", methods=["GET"])
@login_required
def get_items():
    return jsonify(load_data())


@app.route("/api/items", methods=["POST"])
@login_required
def add_item():
    d = request.json
    rows = load_data()
    shipping = float(d["shipping_fee"])
    price = float(d["customer_price"])
    profit = price - shipping
    new_id = str(int(rows[-1]["id"]) + 1) if rows else "1"
    row = {
        "id": new_id,
        "item_name": d["item_name"],
        "tracking_number": d["tracking_number"],
        "customer_name": d.get("customer_name", ""),
        "shipping_fee": f"{shipping:.2f}",
        "customer_price": f"{price:.2f}",
        "profit": f"{profit:.2f}",
        "date_added": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    rows.append(row)
    save_data(rows)
    return jsonify({"success": True, "item": row})


@app.route("/api/items/<item_id>", methods=["PUT"])
@login_required
def edit_item(item_id):
    d = request.json
    rows = load_data()
    for row in rows:
        if row["id"] == item_id:
            shipping = float(d["shipping_fee"])
            price = float(d["customer_price"])
            profit = price - shipping
            row["item_name"]       = d["item_name"]
            row["tracking_number"] = d["tracking_number"]
            row["customer_name"]   = d.get("customer_name", "")
            row["shipping_fee"]    = f"{shipping:.2f}"
            row["customer_price"]  = f"{price:.2f}"
            row["profit"]          = f"{profit:.2f}"
            save_data(rows)
            return jsonify({"success": True, "item": row})
    return jsonify({"success": False}), 404


@app.route("/api/items/<item_id>", methods=["DELETE"])
@login_required
def delete_item(item_id):
    rows = load_data()
    rows = [r for r in rows if r["id"] != item_id]
    save_data(rows)
    return jsonify({"success": True})


@app.route("/api/export")
@login_required
def export_csv():
    rows = load_data()
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(rows)
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype="text/csv",
        as_attachment=True,
        download_name=f"import_tracker_{datetime.now().strftime('%Y%m%d')}.csv"
    )


if __name__ == "__main__":
    print("\n✅ Import Tracker is running!")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=False)
