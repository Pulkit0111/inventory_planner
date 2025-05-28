from langchain_community.utilities import SQLDatabase
from langchain_experimental.sql import SQLDatabaseChain
from langchain_openai import OpenAI
from dotenv import load_dotenv
import os

def setup_database():
    """Initialize the database connection and chain."""
    # Load environment variables
    load_dotenv()
    
    # Check if database file exists
    # db_path = "data/retailware.db"
    db_path = "postgresql://neondb_owner:npg_XGOPds3E8HAw@ep-wild-silence-a8syvnc1-pooler.eastus2.azure.neon.tech/neondb?sslmode=require"
    # if not os.path.exists(db_path):
    #     raise FileNotFoundError(f"Database file not found at {db_path}")
    
    # Create LangChain SQLDatabase object
    db = SQLDatabase.from_uri(db_path)
    
    # Connect to OpenAI LLM with temperature 0 for deterministic output
    llm = OpenAI(model="gpt-4o-mini", temperature=0)
    
    # Create the SQLDatabaseChain with verbose output
    return SQLDatabaseChain.from_llm(llm, db, verbose=True)

def main():
    """Main function to run the inventory chat interface."""
    try:
        # Setup the database chain
        db_chain = setup_database()
        
        print("\n📦 Welcome to Inventory Chat Assistant!")
        print("Ask questions about your inventory in natural language.")
        print("Type 'exit', 'quit', 'bye', or 'stop' to end the session.")
        print("--------------------------------")
        
        while True:
            question = input("\nYou: ").strip()
            
            if question.lower() in ["exit", "quit", "bye", "stop"]:
                print("\n👋 Thank you for using Inventory Chat Assistant!")
                break
                
            if not question:
                print("Please enter a question.")
                continue
                
            try:
                response = db_chain.invoke(question)
                print("\nInventory:", response["result"])
                print("--------------------------------")
            except Exception as e:
                print(f"\n⚠️ Error: {str(e)}")
                print("Please try rephrasing your question.")
                
    except Exception as e:
        print(f"\n❌ Error initializing the application: {str(e)}")
        print("Please make sure:")
        print("1. Your .env file contains the OPENAI_API_KEY")
        print("2. The database file exists at data/retailware.db")
        print("3. You have all required dependencies installed")

if __name__ == "__main__":
    main()
