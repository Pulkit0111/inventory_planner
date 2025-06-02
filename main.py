from langchain_community.utilities import SQLDatabase
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv
from sqlalchemy import inspect
# from langchain.chains import LLMChain
from langchain_core.output_parsers import StrOutputParser
import os
import re

load_dotenv()

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
db = SQLDatabase.from_uri(os.getenv("DB_PATH"))
embedding_model = OpenAIEmbeddings(model="text-embedding-3-small")

engine = db._engine  # or db._engine if it’s private
inspector = inspect(engine)

# ---------------------------------------------------------------------------------------------
# --------------Getting the Schema of all the tables, chunking and embedding them--------------
# ---------------------------------------------------------------------------------------------
# def get_table_schema(table_name: str):
#     """
#     - Uses SQLAlchemy inspector to get column metadata (DB-agnostic).
#     - Uses TOP for SQL Server, LIMIT otherwise, to grab sample rows.
#     """
#     try:
#         # Columns via inspector
#         cols_info = inspector.get_columns(table_name)
#         parsed_columns = [
#             {
#                 "column_name": col["name"],
#                 "data_type": str(col["type"]),
#                 "nullable": col["nullable"],
#                 "default": col.get("default"),
#             }
#             for col in cols_info
#         ]

#         # Sample data: SQL Server needs TOP
#         if engine.dialect.name.lower() in ("mssql", "microsoft sql server"):
#             sample = db.run(f"SELECT TOP 3 * FROM {table_name}")
#         else:
#             sample = db.run(f"SELECT * FROM {table_name} LIMIT 3")

#         return {
#             "table_name": table_name,
#             "columns": parsed_columns,
#             "sample_data": sample
#         }

#     except Exception as e:
#         print(f"Warning: Error getting schema for {table_name}: {e}")
#         return None

    
# # Get detailed schema information for all tables
# schema_docs = []
# for table in db.get_usable_table_names():
#     if table.startswith('_xlnm'):  # Skip Excel filter tables
#         continue

#     info = get_table_schema(table)
#     if not info:
#         continue

#     # format columns
#     cols_text = "\n".join(
#         f"- {col['column_name']} ({col['data_type']}, nullable={col['nullable']})"
#         for col in info["columns"]
#     )

#     # format sample rows (limit to 2)
#     samples = info["sample_data"][:2]
#     sample_text = "\n".join(str(row) for row in samples)

#     content = (
#         f"Table: {table}\n\n"
#         f"Columns:\n{cols_text}\n\n"
#         f"Sample Rows:\n{sample_text}"
#     )

#     schema_docs.append(Document(page_content=content, metadata={"table": table}))
    
# # Embed & index
# vector_index = FAISS.from_documents(schema_docs, embedding_model)

# # Persist the FAISS index to disk so you don't rebuild it every run
# vector_index.save_local("faiss_schema_index")
def get_table_schema(table_name):
    """
    This function gets information about a database table:
    - The columns and their details (name, type, nullable, default)
    - A few sample rows from the table
    
    It works for different databases by adjusting the sample query.
    """
    try:
        # Get column information using the inspector
        cols_info = inspector.get_columns(table_name)
        
        # Create an empty list to store column details
        parsed_columns = []
        
        # Loop through each column info dictionary
        for col in cols_info:
            # Create a simple dictionary with the details we want
            col_details = {
                "column_name": col["name"],
                "data_type": str(col["type"]),
                "nullable": col["nullable"],
                "default": col.get("default"),
            }
            # Add this dictionary to our list
            parsed_columns.append(col_details)

        # Get sample rows from the table
        # SQL Server uses 'TOP', others use 'LIMIT'
        if engine.dialect.name.lower() in ("mssql", "microsoft sql server"):
            sample = db.run(f"SELECT TOP 3 * FROM {table_name}")
        else:
            sample = db.run(f"SELECT * FROM {table_name} LIMIT 3")

        # Return all the collected info as a dictionary
        return {
            "table_name": table_name,
            "columns": parsed_columns,
            "sample_data": sample
        }

    except Exception as e:
        # If something goes wrong, print a warning and return None
        print(f"Warning: Error getting schema for {table_name}: {e}")
        return None

# Create an empty list to hold schema documents
schema_docs = []

# Get all usable table names from the database
all_tables = db.get_usable_table_names()

# Loop through each table name
for table in all_tables:
    # Skip tables that start with '_xlnm' (Excel filter tables)
    if table.startswith('_xlnm'):
        continue

    # Get schema info for the current table
    info = get_table_schema(table)
    
    # If info is None (error), skip this table
    if not info:
        continue

    # Format the columns into a readable string
    cols_text = ""
    for col in info["columns"]:
        cols_text += f"- {col['column_name']} ({col['data_type']}, nullable={col['nullable']})\n"

    # Take only the first 2 sample rows to keep it short
    samples = info["sample_data"][:2]

    # Convert each sample row to string and join with new lines
    sample_text = ""
    for row in samples:
        sample_text += str(row) + "\n"

    # Combine all parts into one content string
    content = (
        f"Table: {table}\n\n"
        f"Columns:\n{cols_text}\n"
        f"Sample Rows:\n{sample_text}"
    )

    # Create a Document object with the content and metadata
    doc = Document(page_content=content, metadata={"table": table})

    # Add this document to our list
    schema_docs.append(doc)

# Now, create a vector index from these documents using the embedding model
vector_index = FAISS.from_documents(schema_docs, embedding_model)

# Save the index locally so we don't have to rebuild it every time
vector_index.save_local("faiss_schema_index")
# ---------------------------------------------------------------------------------------------
# --------------Getting the Schema of all the tables, chunking and embedding them--------------
# ---------------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------------
# --------------Retrieving the schema of the tables and generating the sql query---------------
# ---------------------------------------------------------------------------------------------
retriever = vector_index.as_retriever(search_kwargs={"k": 3})

# SQL-generation prompt
sql_prompt = ChatPromptTemplate.from_template("""
You are an expert SQL generator.
You have access to the following table schemas (only the most relevant ones are shown):

{schemas}

QUESTION:
{question}

Write ONLY the SQL query, with no explanation or code fences.
""")

# Wrap in an LLMChain
# sql_chain = LLMChain(
#     llm=llm,
#     prompt=sql_prompt,
#     # verbose=True
# )
sql_chain = sql_prompt | llm | StrOutputParser()

# # Test retrieval + SQL generation
# question = "Give me the list of top 5 products that have a stock level below 10"
# # Retrieve the most relevant schema docs
# docs = retriever.get_relevant_documents(question)
# print("Retrieved tables:", [d.metadata["table"] for d in docs])

# # Assemble the schemas and run the chain
# schemas_text = "\n\n".join(d.page_content for d in docs)
# raw_sql = sql_chain.invoke({"schemas": schemas_text, "question": question})["text"]
# clean_sql = re.sub(r"^```sql\s*|```$", "", raw_sql, flags=re.IGNORECASE).strip()
# print("Generated SQL:\n", clean_sql)

# # Run the SQL query
# result = db.run(clean_sql)
# print("SQL Result:\n", result)

# Generate SQL query tool
@tool
def generate_sql(question):
    """
    Converts a natural language question into a pure SQL query using the schema.
    Generates only the SQL query with no explanation.
    """
    # docs = retriever.get_relevant_documents(question)
    docs = retriever.invoke(question)
    schemas = "\n\n".join(d.page_content for d in docs)
    raw = sql_chain.invoke({"schemas": schemas, "question": question})
    return re.sub(r"^```sql\s*|```$", "", raw, flags=re.IGNORECASE).strip()
# ---------------------------------------------------------------------------------------------
# --------------Retrieving the schema of the tables and generating the sql query---------------
# ---------------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------------
# --------------Execute the SQL and generate a natural‐language explanation--------------------
# ---------------------------------------------------------------------------------------------
explanation_prompt = ChatPromptTemplate.from_template("""
You are a helpful assistant.  
Here is a SQL query and its output.  
Write a clear, concise natural‐language answer explaining what the result means:

SQL QUERY:
{query}

RESULT:
{result}

Answer:
""")

# # Wrap it in an LLMChain
# explain_chain = LLMChain(
#     llm=llm,
#     prompt=explanation_prompt,
#     # verbose=True
# )
explain_chain = explanation_prompt | llm | StrOutputParser()

# # Test it
# # Pick a question and generate SQL
# question = "Give me the list of top 5 products that have a stock level below 10"
# sql = generate_sql(question)
# print("Generated SQL:\n", sql)

# # Execute it
# result = db.run(sql)
# print("Raw result:", result)

# # Explain it
# explanation = explain_chain.invoke({"query": sql, "result": result})["text"]
# print("Explanation:\n", explanation)

# Natural language explanation tool
@tool
def sql_result_to_answer(sql_query):
    """
    Runs the given SQL query on the database, then generates
    a natural‐language answer explaining the results.
    """
    result = db.run(sql_query)
    return explain_chain.invoke({"query": sql_query, "result": result})
# ---------------------------------------------------------------------------------------------
# --------------Execute the SQL and generate a natural‐language explanation--------------------
# ---------------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------------
# ------------------------- Combine the tools into an agent------------------------------------
# ---------------------------------------------------------------------------------------------
tools = [generate_sql, sql_result_to_answer]

# Create a memory saver (optional, but useful)
memory = MemorySaver()

# Build the REACT agent
agent = create_react_agent(
    llm,
    tools=tools,
    prompt=f"""
You are an intelligent SQL assistant with access to a database.  
When a user asks a question, follow exactly two steps:  
1. Use the `generate_sql` tool to convert the user’s question into a SQL query (no explanation).  
2. Use the `sql_result_to_answer` tool to run that SQL and return a natural‐language answer.

Be concise and precise. Only use each tool once per question.
""",
    checkpointer=memory
)
# ---------------------------------------------------------------------------------------------
# ------------------------- Combine the tools into an agent------------------------------------
# ---------------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------------
# ----------------------------------RAG Chatbot------------------------------------------------
# ---------------------------------------------------------------------------------------------
print("SQL BOT: Hi, I’m your SQL assistant. How can I help you today?\n")

while True:
    user_query = input("You: ")
    if user_query.lower() in ["exit", "quit", "bye", "stop"]:
        print("SQL BOT: Goodbye!")
        break

    response = agent.invoke(
        {"messages": [HumanMessage(content=user_query)]},
        {"configurable": {"thread_id": "test_session"}}
    )
    # The agent.invoke call returns a dict with `messages`
    bot_reply = response["messages"][-1].content

    print("\nSQL BOT:", bot_reply, "\n")
# ---------------------------------------------------------------------------------------------
# ----------------------------------RAG Chatbot------------------------------------------------
# ---------------------------------------------------------------------------------------------