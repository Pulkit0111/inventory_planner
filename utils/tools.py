import csv

CSV_PATH = "data/inventory.csv"

def calculate_reorder_cost(product_name: str, buffer=5) -> str:
    try:
        with open(CSV_PATH, "r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row["Product"].lower().strip() == product_name.lower().strip():
                    stock = int(row["Stock"])
                    threshold = int(row["Reorder Threshold"])
                    unit_price = int(row["Unit Price (INR)"])

                    if stock >= threshold:
                        return f"✅ {product_name} is sufficiently stocked. No reorder needed."

                    qty = (threshold - stock) + buffer
                    total_cost = qty * unit_price

                    return (
                        f"🧮 Reorder Cost for {product_name}:\n"
                        f"- Units to Order: {qty}\n"
                        f"- Unit Price: ₹{unit_price}\n"
                        f"- Total Estimated Cost: ₹{total_cost}"
                    )
        return f"❌ Product '{product_name}' not found in inventory."
    except Exception as e:
        return f"⚠️ Error calculating reorder cost: {e}"