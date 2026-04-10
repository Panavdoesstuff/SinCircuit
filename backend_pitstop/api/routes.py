from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from api.schemas import RaceState # Import from your schemas.py
from agents.debate_graph import run_debate # Your LangGraph
import uuid
import json
import asyncio

router = APIRouter()
races = {}  # Live memory store

@router.post("/start")
def start_race():
    race_id = str(uuid.uuid4())[:8]
    races[race_id] = RaceState() # Ensure RaceState is defined in schemas.py
    return {"race_id": race_id, "state": races[race_id].to_dict()}

@router.post("/{race_id}/tick")
def tick_race(race_id: str):
    if race_id not in races:
        raise HTTPException(status_code=404, detail="Race not found")
    races[race_id].tick()
    return {"state": races[race_id].to_dict()}

@router.post("/{race_id}/pit")
def pit_stop(race_id: str, compound: str = "hard"):
    if race_id not in races:
        raise HTTPException(status_code=404, detail="Race not found")
    races[race_id].pit(compound)
    return {"state": races[race_id].to_dict()}

async def debate_stream(race_id: str):
    if race_id not in races:
        yield f"data: {json.dumps({'error': 'not found'})}\n\n"
        return

    race_data = races[race_id].to_dict()
    result = run_debate(race_data)

    agents_order = ["engineer", "tyre", "weather", "rival", "synthesiser"]
    agent_labels = {
        "engineer": "Race Engineer",
        "tyre": "Tyre Strategist",
        "weather": "Weather Oracle",
        "rival": "Rival Analyst",
        "synthesiser": "Pit Wall Director"
    }
    
    rec_map = {
        "engineer": result["engineer_rec"],
        "tyre": result["tyre_rec"],
        "weather": result["weather_rec"],
        "rival": result["rival_rec"],
        "synthesiser": result["final_decision"]
    }

    for agent_key in agents_order:
        text = rec_map[agent_key]
        # Stream word by word for the "AI typing" effect
        for word in text.split(" "):
            chunk = {"agent": agent_labels[agent_key], "token": word + " ", "final": False}
            yield f"data: {json.dumps(chunk)}\n\n"
            await asyncio.sleep(0.03) # Speed adjusted for smoothness
        
        # Send a "final" chunk for this specific agent
        yield f"data: {json.dumps({'agent': agent_labels[agent_key], 'final': True, 'full_text': text})}\n\n"
        await asyncio.sleep(0.2)

@router.get("/{race_id}/stream")
async def stream_debate(race_id: str):
    return StreamingResponse(debate_stream(race_id), media_type="text/event-stream")