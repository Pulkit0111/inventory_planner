from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from .models import embeddings
from .loader import load_inventory_data

def create_inventory_index(persist_directory: str = "data/inventory_faiss_index"):
    # Load inventory data
    documents = load_inventory_data()

    # Split documents into chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=50)
    chunks = text_splitter.split_documents(documents)
    
    # Create FAISS index
    db = FAISS.from_documents(chunks, embeddings)

    # Save index to disk
    db.save_local(persist_directory)
