from langchain_community.utilities import SQLDatabase
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
import os
import re

load_dotenv()

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
db = SQLDatabase.from_uri(os.getenv("DB_PATH"))

def get_table_schema(table_name):
    """Get detailed schema information for a table"""
    try:
        # Get column information using SQL Server specific query
        schema_query = f"""
        SELECT 
            c.name AS column_name,
            t.name AS data_type,
            c.max_length,
            c.precision,
            c.scale,
            c.is_nullable
        FROM sys.columns c
        INNER JOIN sys.types t ON c.user_type_id = t.user_type_id
        WHERE c.object_id = OBJECT_ID('{table_name}')
        """
        
        columns = db.run(schema_query)
        
        # Get sample data using SQL Server TOP clause
        sample = db.run(f"SELECT TOP 3 * FROM {table_name}")
        
        return {
            "table_name": table_name,
            "columns": columns,
            "sample_data": sample
        }
    except Exception as e:
        print(f"Warning: Error getting schema for {table_name}: {str(e)}")
        return None

# Get detailed schema information for all tables
schema_info = {}
for table in db.get_usable_table_names():
    if not table.startswith('_xlnm'):  # Skip Excel filter tables
        schema = get_table_schema(table)
        if schema:  # Only add if schema retrieval was successful
            schema_info[table] = schema

# Format schema information for the prompt
formatted_schema = "\n\n".join([
    f"Table: {table}\nSchema:\n{info['columns']}\nSample Data:\n{info['sample_data']}"
    for table, info in schema_info.items()
    if info is not None  # Only include tables with valid schema
])

if not formatted_schema:
    print("Warning: No valid schema information could be retrieved from the database.")
    formatted_schema = "No schema information available. Please check database connection and permissions."

# Print the database dialect for debugging
print(f"Database dialect: {db.dialect}")

# prompt to generate only the sql query
prompt = ChatPromptTemplate.from_template("""
You are an expert SQL generator. Use the following database schema and sample data to write an accurate SQL query.
Write only the SQL query with no explanation.

DATABASE SCHEMA AND SAMPLE DATA:
{schema}

QUESTION:
{question}

SQL Query:
""")

# prompt to generate the explanation from the sql query and the result
response_prompt = ChatPromptTemplate.from_template("""
You are a helpful assistant. Here is a SQL query and its output. Write a clear natural final response with the answer to the question with proper explanation.

SQL QUERY:
{query}

RESULT:
{result}

EXPLANATION:
""")

@tool
def generate_sql(question):
    """
    Converts a natural language question into a pure SQL query using the schema.
    Generates only the SQL query with no explanation.
    """
    formatted_prompt = prompt.format(schema=formatted_schema, question=question)
    sql_response = llm.invoke(formatted_prompt)
    raw_sql = sql_response.content.strip()
    # Remove Markdown SQL code block if present
    cleaned_sql = re.sub(r"^```sql\s*|```$", "", raw_sql, flags=re.IGNORECASE).strip()
    return cleaned_sql

@tool
def sql_result_to_answer(sql):
    """
    Runs SQL and generates a final natural language answer.
    """
    result = db.run(sql)
    formatted = response_prompt.format(query=sql, result=result)
    return llm.invoke(formatted).content.strip()

memory = MemorySaver()

agent = create_react_agent(
    llm,
    tools=[generate_sql, sql_result_to_answer],
    prompt=f"""
You are an intelligent SQL assistant with access to the following database schema and sample data:
{formatted_schema}

You can use the following tools to answer the user's question:
1. generate_sql: Use this to translate the user's question into SQL. This tool will return only the SQL query.
2. sql_result_to_answer: Use this to run the SQL query and get a natural language explanation of the results.

Follow these steps:
1. First, use generate_sql to create the SQL query
2. Then, use sql_result_to_answer to run the query and get the explanation
3. Provide the final answer to the user

Be precise and avoid unnecessary tool calls. Each question should be answered with exactly two tool calls: one for generating SQL and one for getting the result.
""",
    checkpointer=memory
)

print("SQL BOT: Hi, I'm your SQL assistant. How can I help you today?")
while True:
    question = input("You: ")
    if question.lower() in ["exit", "bye", "stop"]:
        print("SQL BOT: Goodbye!")
        break

    try:
        messages = [HumanMessage(content=question)]
        response = agent.invoke(
            {"messages": messages},
            {"configurable": {"thread_id": "default_session", "recursion_limit": 50}}
        )
        print("SQL BOT:", response["messages"][-1].content)
    except Exception as e:
        print(f"SQL BOT: I encountered an error while processing your request: {str(e)}")
        print("Please try rephrasing your question or ask something else.")

