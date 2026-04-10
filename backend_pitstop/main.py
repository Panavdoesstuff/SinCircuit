import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Internal Imports
from models import RaceState 
from agents.debate_orchestrator import run_debate

app = FastAPI(title="SinCircuit AI Engine")

# --- CORS SETUP ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize global race state
active_race = RaceState()

@app.get("/")
def read_root():
    return {"status": "Engine Online"}

@app.get("/state")
async def get_state():
    return active_race.to_dict()

@app.post("/tick")
async def next_lap():
    active_race.tick()
    return active_race.to_dict()

@app.post("/pit")
async def pit_stop(compound: str):
    active_race.pit(compound)
    return active_race.to_dict()

@app.post("/debate")
async def start_debate():
    try:
        # 1. Get current race data
        state = active_race.to_dict()
        
        # 2. Run the LangGraph Orchestrator
        result = run_debate(state)
        
        # 3. Return full multi-agent breakdown
        return {
            "success": True,
            "state": state,
            "race_engineer": result["engineer_rec"],
            "tyre_specialist": result["tyre_rec"],
            "weather_oracle": result["weather_rec"],
            "rival_analyst": result["rival_rec"],
            "final_decision": result["final_decision"],
            "confidence": result["confidence"],
            "historical_evidence": result["rag_context"]
        }
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        return {"success": False, "error": str(e)}