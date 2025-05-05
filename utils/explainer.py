import csv
from langchain_core.prompts import ChatPromptTemplate
from .models import llm

CSV_PATH = "data/inventory.csv"

prompt_template = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a helpful assistant that answers the inventory related questions in a friendly manner."),
        ("user", """
            Based on the following details:
            Product: {product}
            Stock Level: {stock}
            Reorder Threshold: {threshold}
            Notes: {notes}
            Margin: {margin}
            Unit Price: {unit_price}
            
            Q: Should this product be reordered? Why or why not clearly explain with clear reasoning?
            Answer in a friendly and clear tone and in the following format:
            Reorder: Yes or No
            Reasoning: [Reasoning]
        """),
    ]
)

def get_data(product_name: str) -> dict:
    try:
        with open(CSV_PATH, "r") as file:
            try:
                reader = csv.DictReader(file)
                for row in reader:
                    if row["Product"].lower().strip() == product_name.lower().strip():
                        return {
                            "product": row["Product"],
                            "stock": row["Stock"],
                            "threshold": row["Reorder Threshold"],
                            "notes": row["Notes"],
                            "margin": row["Margin"],
                            "unit_price": row["Unit Price (INR)"],
                        }
                return None
            except csv.Error as e:
                raise Exception(f"Error reading CSV file: {e}")
    except FileNotFoundError:
        raise Exception(f"Inventory file not found at {CSV_PATH}")
    except Exception as e:
        raise Exception(f"Unexpected error accessing inventory file: {e}")

def explain_product(product_name: str) -> str:
    try:
        data = get_data(product_name)
        if data:
            try:
                prompt = prompt_template.format(**data)
                response = llm.invoke(prompt)
                return response.content
            except Exception as e:
                return f"⚠️ Error generating explanation: {e}"
        else:
            return f"❌ Product '{product_name}' not found in inventory."
    except Exception as e:
        return f"⚠️ Error accessing product data: {e}"
