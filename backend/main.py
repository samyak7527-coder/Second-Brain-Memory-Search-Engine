from fastapi import FastAPI
from ingest import ingest_text
from rag import generate_answer

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Second Brain API running"}

@app.post("/ingest")
def ingest(data: dict):
    text = data["text"]
    return ingest_text(text)

@app.post("/query")
def query(data: dict):
    question = data["question"]
    answer = generate_answer(question)
    return {"answer": answer}