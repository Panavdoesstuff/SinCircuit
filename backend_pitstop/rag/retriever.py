import os
import chromadb
from sentence_transformers import SentenceTransformer

# Absolute pathing so it finds your EXISTING chroma_data
current_dir = os.path.dirname(os.path.abspath(__file__))
CHROMA_PATH = os.path.join(current_dir, "..", "chroma_data")

client = chromadb.PersistentClient(path=CHROMA_PATH)
# This MUST match the name in your successful ingest
collection = client.get_or_create_collection("f1_strategies")
model = SentenceTransformer('all-MiniLM-L6-v2')

def get_strategy_context(lap, compound, tyre_age, gap):
    # We ignore 'weather' here because your ingest didn't save it.
    # We force the query to look like your ingested strings.
    query = f"Lap {lap}, {compound} tyres aged {tyre_age} laps"
    
    embedding = model.encode([query])[0].tolist()
    results = collection.query(query_embeddings=[embedding], n_results=3)
    
    # Return the documents found in your existing DB
    return results['documents'][0] if results['documents'] else ["No historical data found."]