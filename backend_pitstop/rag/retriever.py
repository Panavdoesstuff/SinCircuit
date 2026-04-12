import os
import chromadb
from sentence_transformers import SentenceTransformer

# ─────────────────────────────────────────────────────────────────────────────
# Setup Paths & Persistence
# ─────────────────────────────────────────────────────────────────────────────
current_dir = os.path.dirname(os.path.abspath(__file__))
# Ensure this points to the SAME chroma_data folder created by ingest.py
CHROMA_PATH = os.getenv("CHROMA_PATH", os.path.join(current_dir, "..", "chroma_data"))

# Initialize Chroma and the Embedding Model
_client = chromadb.PersistentClient(path=CHROMA_PATH)
_collection = _client.get_or_create_collection(
    "f1_strategies",
    metadata={"hnsw:space": "cosine"}
)
_model = SentenceTransformer("all-MiniLM-L6-v2")

# ─────────────────────────────────────────────────────────────────────────────
# The Retrieval Function
# ─────────────────────────────────────────────────────────────────────────────

def get_strategy_context(lap: int, compound: str, tyre_age: int, 
                          gap: float, laps_remaining: int = 0, 
                          weather: str = "dry") -> list[str]:
    """
    Retrieve the 3 most historically similar F1 race scenarios.
    Returns list of scenario strings to inject as agent context.
    """
    # Create the query string (Must match the format used in ingest.py)
    query = (
        f"Lap {lap}, {compound} tyres aged {tyre_age} laps, "
        f"gap to leader {gap:.1f}s, weather {weather}, "
        f"{laps_remaining} laps remaining"
    )
    
    # Generate embedding for the query
    embedding = _model.encode([query])[0].tolist()
    
    try:
        # Query the vector database
        results = _collection.query(
            query_embeddings=[embedding],
            n_results=3,
            include=["documents", "metadatas", "distances"],
        )
        
        docs = results["documents"][0] if results["documents"] else []
        distances = results["distances"][0] if results["distances"] else []
        
        # Format the matches with a similarity percentage
        formatted = []
        for doc, dist in zip(docs, distances):
            # dist is cosine distance; similarity = 1 - distance
            similarity = round((1 - dist) * 100, 1)
            formatted.append(f"[{similarity}% match] {doc}")
            
        return formatted if formatted else ["No historical data found in ChromaDB."]
        
    except Exception as e:
        return [f"RAG retrieval error: {str(e)}"]

def get_circuit_history(circuit_name: str) -> list[str]:
    """Get historical scenarios specifically from a named circuit."""
    try:
        results = _collection.query(
            query_texts=[f"strategy at {circuit_name}"],
            n_results=5,
            where={"circuit": {"$eq": circuit_name}},
            include=["documents"],
        )
        return results["documents"][0] if results["documents"] else []
    except Exception:
        return []