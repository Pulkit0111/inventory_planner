from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

load_dotenv()

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
llm = ChatOpenAI(model="gpt-4o-mini")

prompt = ChatPromptTemplate.from_template(
    """
    You are a helpful assistant that can answer questions about the inventory.
    You are given a question and context. You job is to only answer the question based on the provided context. If you don't know the answer, say "I don't know", instead of guessing.
    Question: {question}
    Context: {context}
    Answer:
    """
)
