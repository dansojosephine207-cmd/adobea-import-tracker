from flask import Flask, render_template, request, jsonify, send_file
import csv, os, io
from datetime import datetime

app = Flask(__name__)
DATA_FILE = "data.csv"
FIELDS = ["id", "item_name", "tracking_number", "shipping_fee", "customer_price", "profit", "date_added"]

def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    rows = []
    with open(DATA_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows

def save_data(rows):
    with open(DATA_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/items", methods=["GET"])
def get_items():
    return jsonify(load_data())

@app.route("/api/items", methods=["POST"])
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
        "shipping_fee": f"{shipping:.2f}",
        "customer_price": f"{price:.2f}",
        "profit": f"{profit:.2f}",
        "date_added": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    rows.append(row)
    save_data(rows)
    return jsonify({"success": True, "item": row})

@app.route("/api/items/<item_id>", methods=["PUT"])
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
            row["shipping_fee"]    = f"{shipping:.2f}"
            row["customer_price"]  = f"{price:.2f}"
            row["profit"]          = f"{profit:.2f}"
            save_data(rows)
            return jsonify({"success": True, "item": row})
    return jsonify({"success": False}), 404

@app.route("/api/items/<item_id>", methods=["DELETE"])
def delete_item(item_id):
    rows = load_data()
    rows = [r for r in rows if r["id"] != item_id]
    save_data(rows)
    return jsonify({"success": True})

@app.route("/api/export")
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
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)