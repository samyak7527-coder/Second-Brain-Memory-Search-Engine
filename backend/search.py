from db import collection, get_embedding

def search(query):
    query_embedding = get_embedding(query)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=5
    )

    return results['documents'][0]