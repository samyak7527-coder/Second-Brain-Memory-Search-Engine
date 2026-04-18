from search import search
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()

# Get API key from environment
groq_api_key = os.getenv("GROQ_API_KEY")

# Initialize Groq model
llm = ChatGroq(
    api_key=groq_api_key,
    model_name="openai/gpt-oss-120b"
)

def generate_answer(query):
    docs = search(query)

    context = "\n".join(docs)

    prompt = f"""
    Answer using context only.

    Context:
    {context}

    Question:
    {query}
    """

    response = llm.invoke([HumanMessage(content=prompt)])

    return response.content