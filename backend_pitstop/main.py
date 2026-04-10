import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Internal Imports
from models import RaceState 
from rag.retriever import get_strategy_context
from api.groq_client import get_agent_response
from agents.race_engineer import race_engineer_agent
from agents.debate_orchestrator import run_debate

app = FastAPI(title="SinCircuit AI Engine")

# --- CORS SETUP (So React can talk to this) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🏎️ INITIALIZE THE LIVE STATE
# This stays in memory while the server is running
active_race = RaceState()

# --- ROUTES ---

@app.get("/")
def read_root():
    return {"status": "Engine Online"}

@app.get("/state")
async def get_state():
    """Returns the current raw data of the race"""
    return active_race.to_dict()

@app.post("/tick")
async def next_lap():
    """Moves the race forward by 1 lap and updates tyre wear/gaps"""
    active_race.tick()
    return active_race.to_dict()

@app.post("/pit")
async def pit_stop(compound: str):
    """Executes a pit stop and resets tyre age"""
    active_race.pit(compound)
    return active_race.to_dict()

@app.post("/debate")
async def start_debate():
    try:
        # 1. Get the current race state math
        state = active_race.to_dict()
        
        # 2. Run the LangGraph Orchestrator
        # This one line handles RAG and all 4 agents in order
        debate_result = run_debate(state)
        
        # 3. Return the compiled results to your frontend
        return {
            "success": True,
            "state": state,
            "race_engineer": debate_result["engineer_rec"],
            "tyre_strategist": debate_result["tyre_rec"],
            "weather_oracle": debate_result["weather_rec"],
            "rival_analyst": debate_result["rival_rec"],
            "final_decision": debate_result["final_decision"],
            "confidence": debate_result["confidence"],
            "historical_evidence": debate_result["rag_context"]
        }
    except Exception as e:
        return {"success": False, "error": str(e)}