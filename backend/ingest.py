from db import collection, get_embedding
import uuid
import datetime

def chunk_text(text, chunk_size=500):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i+chunk_size])
        chunks.append(chunk)
    return chunks


def ingest_text(text, source: str = "manual"):
    chunks = chunk_text(text)
    # Unix timestamp stored as metadata — lets us filter by date window later
    ingested_at = int(datetime.datetime.now().timestamp())

    for chunk in chunks:
        embedding = get_embedding(chunk)
        collection.add(
            documents=[chunk],
            embeddings=[embedding],
            ids=[str(uuid.uuid4())],
            metadatas=[{
                "ingested_at": ingested_at,   # integer Unix timestamp
                "source": source,             # "manual" | "pdf" | "pptx"
            }]
        )

    return {"status": "stored", "chunks": len(chunks)}