import chromadb
from sentence_transformers import SentenceTransformer
import os

# Load embedding model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Initialize ChromaDB with persistent storage
db_path = os.path.join(os.path.dirname(__file__), '..', 'chroma_db')
os.makedirs(db_path, exist_ok=True)

client = chromadb.HttpClient() if os.getenv('CHROMA_HOST') else chromadb.PersistentClient(path=db_path)

try:
    collection = client.get_collection(name="notes")
except Exception:
    collection = client.create_collection(name="notes")

def get_embedding(text):
    return model.encode(text).tolist()