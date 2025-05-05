from utils.retriever import inventory_qa_chain
from utils.tools import calculate_reorder_cost
from utils.explainer import explain_product

def show_menu():
    print("\n📦 Welcome to Smart Inventory Assistant")
    print("Choose an option:")
    print("1. Ask about inventory (RAG)")
    print("2. Estimate reorder cost")
    print("3. Explain reorder decision")
    print("4. Exit")

def main():

    while True:
        show_menu()
        choice = input("\nEnter choice (1–4): ").strip()

        if choice == "1":
            query = input("❓ Ask a question: ")
            result = inventory_qa_chain.invoke(query)
            print("\n💬 Answer:\n", result)

        elif choice == "2":
            product = input("📦 Enter product name: ")
            print("\n" + calculate_reorder_cost(product))

        elif choice == "3":
            product = input("📦 Enter product name: ")
            print("\n" + explain_product(product))

        elif choice == "4":
            print("👋 Exiting. Thank you!")
            break
        else:
            print("⚠️ Invalid input. Try again.")

if __name__ == "__main__":
    main()
