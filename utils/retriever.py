import os
from .indexer import create_inventory_index
from .models import prompt, llm, embeddings
from langchain_community.vectorstores import FAISS
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

def get_vector_db(path="data/inventory_faiss_index"):
        # Check if vector store exists
    if os.path.exists(path):
        print(f"✅ Vector store found at {path}")
        return FAISS.load_local(path, embeddings, allow_dangerous_deserialization=True)
    else:
        # Create new index if it doesn't exist
        create_inventory_index(path)
        print(f"✅ Vector store created at {path}")
        return FAISS.load_local(path, embeddings, allow_dangerous_deserialization=True)
    
def build_inventory_qa_chain():
    db = get_vector_db()
    retriever = db.as_retriever()
    
    return (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
inventory_qa_chain = build_inventory_qa_chain()


