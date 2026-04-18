from db import collection, get_embedding
import uuid

def chunk_text(text, chunk_size=500):
    words = text.split()
    chunks = []
    
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i+chunk_size])
        chunks.append(chunk)
    
    return chunks


def ingest_text(text):
    chunks = chunk_text(text)

    for chunk in chunks:
        embedding = get_embedding(chunk)

        collection.add(
            documents=[chunk],
            embeddings=[embedding],
            ids=[str(uuid.uuid4())]
        )

    return {"status": "stored", "chunks": len(chunks)}