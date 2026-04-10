import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Internal Imports
from models import RaceState 
from rag.retriever import get_strategy_context
from api.groq_client import get_agent_response

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
    """The Big One: Pulls current state, gets RAG context, and runs AI Agents"""
    try:
        # 1. Get current data from our state machine
        state = active_race.to_dict()
        
        # 2. Get 3 historical matches from your RAG (ChromaDB)
        historical_matches = get_strategy_context(
            state["lap"], 
            state["compound"], 
            state["tyre_age"], 
            state["gap_to_leader"]
        )
        
        context_str = "\n".join(historical_matches)
        current_sit = (
            f"Lap {state['lap']}, {state['compound']} tyres ({state['tyre_age']} laps old), "
            f"Gap: {state['gap_to_leader']}s, Weather: {state['weather']}"
        )

        # 3. Trigger the Multi-Agent Debate
        strat_view = get_agent_response("strategist", current_sit, context_str)
        spec_view = get_agent_response("specialist", current_sit, context_str)
        
        # 4. Lead Engineer makes the final call
        debate_summary = f"Strategist: {strat_view}\nSpecialist: {spec_view}"
        final_call = get_agent_response("engineer", current_sit, debate_summary)

        return {
            "success": True,
            "state": state,
            "strategist": strat_view,
            "specialist": spec_view,
            "final_decision": final_call,
            "historical_evidence": historical_matches
        }

    except Exception as e:
        return {"success": False, "error": str(e)}