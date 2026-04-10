from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .rag.retriever import get_strategy_context
from .api.groq_client import get_agent_response

app = FastAPI()

# Allow React to talk to FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class RaceState(BaseModel):
    lap: int
    compound: str
    tyre_age: int
    gap: float

@app.post("/debate")
async def start_debate(state: RaceState):
    try:
        # 1. Pull from your ALREADY LOADED data
        historical_matches = get_strategy_context(
            state.lap, 
            state.compound, 
            state.tyre_age, 
            state.gap
        )
        
        context_str = "\n".join(historical_matches)
        current_situation = (
            f"Current: Lap {state.lap}, {state.compound} tyres "
            f"({state.tyre_age} laps old), Gap: {state.gap}s"
        )

        # 2. Agents debate using that specific context
        strat = get_agent_response("strategist", current_situation, context_str)
        spec = get_agent_response("specialist", current_situation, context_str)
        
        # 3. Final Decision
        final = get_agent_response("engineer", current_situation, f"Strat: {strat}\nSpec: {spec}")

        return {
            "success": True,
            "strategist": strat,
            "specialist": spec,
            "final_decision": final,
            "sources": historical_matches 
        }
    except Exception as e:
        return {"success": False, "error": str(e)}