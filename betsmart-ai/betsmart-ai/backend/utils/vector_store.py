import chromadb
from sentence_transformers import SentenceTransformer
import json

model = SentenceTransformer("all-MiniLM-L6-v2")
client = chromadb.Client()

collection = client.create_collection("betting_knowledge")
cache_collection = client.create_collection("semantic_cache")

def load_data():
    with open("rag_data.txt", "r") as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        emb = model.encode(line).tolist()
        collection.add(
            documents=[line],
            embeddings=[emb],
            ids=[str(i)]
        )

def query_knowledge(query):
    emb = model.encode(query).tolist()
    results = collection.query(
        query_embeddings=[emb],
        n_results=2
    )
    if results["documents"] and len(results["documents"][0]) > 0:
        return results["documents"][0]
    return ""

def check_semantic_cache(query: str, threshold: float = 0.5):
    """Checks the ChromaDB cache for a semantically similar query."""
    emb = model.encode(query).tolist()
    try:
        results = cache_collection.query(
            query_embeddings=[emb],
            n_results=1,
            include=["documents", "distances"]
        )
        if results["distances"] and len(results["distances"][0]) > 0:
            dist = results["distances"][0][0]
            if dist < threshold:
                return results["documents"][0][0]  # Return cached JSON string
    except Exception:
        pass
    return None

def add_to_semantic_cache(query: str, answer_json_str: str):
    """Adds a query and its response to the semantic cache."""
    emb = model.encode(query).tolist()
    import uuid
    doc_id = str(uuid.uuid4())
    try:
        cache_collection.add(
            documents=[answer_json_str],
            embeddings=[emb],
            ids=[doc_id],
            metadatas=[{"query": query}]
        )
    except Exception:
        pass