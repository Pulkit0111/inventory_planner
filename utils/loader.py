from langchain_community.document_loaders.csv_loader import CSVLoader

def load_inventory_data(csv_path: str = "data/inventory.csv") -> list:
    try:
        loader = CSVLoader(file_path = csv_path)
        documents = loader.load()
        return documents
    except Exception as e:
        print(f"Error loading inventory data: {e}")
        return []




