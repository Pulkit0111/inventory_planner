from langchain_community.utilities import SQLDatabase
from langchain_experimental.sql import SQLDatabaseChain
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os
import re

load_dotenv()

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
db = SQLDatabase.from_uri(os.getenv("DB_PATH"))

# Fetch the schema of the database to provide the context for the LLM
schema_info = db.get_table_info()

# prompt to generate only the sql query
prompt = ChatPromptTemplate.from_template("""
You are an expert SQL generator. Given a user's question and schema info, write only the SQL query with no explanation.

SCHEMA:
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

def generate_sql(question: str) -> str:
    formatted_prompt = prompt.format(schema=schema_info, question=question)
    sql_response = llm.invoke(formatted_prompt)
    raw_sql = sql_response.content.strip()
    # Remove Markdown SQL code block if present
    cleaned_sql = re.sub(r"^```sql\s*|```$", "", raw_sql, flags=re.IGNORECASE).strip()
    return cleaned_sql


def run_sql(query):
    return db.run(query)

def generate_explanation(query, result):
    formatted = response_prompt.format(query=query, result=result)
    return llm.invoke(formatted).content.strip()

while True:
    print("SQL BOT: Hi, I'm your SQL assistant. How can I help you today?")
    question = input("You: ")
    if question.lower() in ["exit", "quit", "bye", "stop"]:
        print("SQL BOT: Goodbye!")
        break
    
    sql = generate_sql(question)
    print("SQL BOT: Generated SQL:", sql, "\n")

    data = run_sql(sql)
    print("SQL BOT: Raw Result:", data, "\n")

    final_answer = generate_explanation(sql, data)
    print("SQL BOT: Final Answer:", final_answer, "\n")

