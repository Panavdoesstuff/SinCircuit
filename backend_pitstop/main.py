"""
main.py — Pit Wall AI Backend
Complete rewrite: data-driven 20-car simulation with real F1 race scripts.
"""
import os
import json
import asyncio
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv

load_dotenv()

# ── Conditional import — old models.py as fallback if new sim fails ────────────
try:
    from data.race_library import load_random_script, load_library
    from simulation.race_state import load_from_script, race_state_to_dict, RaceState
    from simulation.field_sim import tick_lap, execute_player_pit
    from simulation.summary import build_summary
    from agents.advice_engine import run_advice_engine
    NEW_SIM = True
except ImportError as e:
    print(f"[WARNING] New simulation import failed ({e}), falling back to legacy models.py")
    from models import RaceState as LegacyRaceState
    NEW_SIM = False

from agents.debate_orchestrator import run_debate

# ── Global state ──────────────────────────────────────────────────────────────
races: dict[str, object] = {}
ws_connections: dict[str, list[WebSocket]] = {}
paused: dict[str, bool] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    races.clear()


app = FastAPI(title="Pit Wall AI — Data-Driven Edition", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── BROADCAST ────────────────────────────────────────────────────────────────

async def broadcast(race_id: str, data: dict):
    if race_id not in ws_connections:
        return
    message = json.dumps(data)
    dead = []
    for ws in ws_connections[race_id]:
        try:
            await ws.send_text(message)
        except Exception:
            dead.append(ws)
    for ws in dead:
        if ws in ws_connections.get(race_id, []):
            ws_connections[race_id].remove(ws)


# ─── RACE LOOP ────────────────────────────────────────────────────────────────

async def race_loop(race_id: str):
    TICK_INTERVAL = 1.5
    while race_id in races:
        if paused.get(race_id, False):
            await asyncio.sleep(0.25)
            continue

        rs = races[race_id]

        if NEW_SIM:
            if rs.finished:
                if rs.race_summary is None:
                    rs.race_summary = build_summary(rs)
                state_dict = race_state_to_dict(rs)
                await broadcast(race_id, {"type": "race_finished", "state": state_dict})
                break

            # Tick one lap — advances all 20 cars
            tick_lap(rs)

            # Run advice engine every lap
            new_advice = run_advice_engine(rs)

            # Check if finished immediately
            if rs.finished:
                if rs.race_summary is None:
                    rs.race_summary = build_summary(rs)
                state_dict = race_state_to_dict(rs)
                await broadcast(race_id, {"type": "race_finished", "state": state_dict})
                break

            state_dict = race_state_to_dict(rs)
            await broadcast(race_id, {
                "type": "tick",
                "state": state_dict,
                "new_advice": new_advice,
            })
        else:
            # Legacy fallback
            if rs.finished:
                await broadcast(race_id, {"type": "race_finished", "state": rs.to_dict()})
                break
            rs.tick()
            await broadcast(race_id, {"type": "tick", "state": rs.to_dict()})

        await asyncio.sleep(TICK_INTERVAL)


# ─── ROUTES ───────────────────────────────────────────────────────────────────

@app.post("/race/start")
async def start_race(background_tasks: BackgroundTasks):
    if NEW_SIM:
        # Verify library exists
        try:
            library = load_library()
            if not library:
                raise HTTPException(
                    status_code=503,
                    detail="Race library is empty. Run: python -m backend_pitstop.data.race_library build"
                )
        except FileNotFoundError as e:
            raise HTTPException(
                status_code=503,
                detail=str(e)
            )

        race_id = str(uuid.uuid4())[:8]
        script = load_random_script()
        rs = load_from_script(script, race_id)

        races[race_id] = rs
        ws_connections[race_id] = []
        paused[race_id] = False
        background_tasks.add_task(race_loop, race_id)

        return {
            "race_id": race_id,
            "state": race_state_to_dict(rs),
            "script_id": script["race_id"],
            "circuit": script["circuit"],
        }
    else:
        # Legacy
        race_id = str(uuid.uuid4())[:8]
        from models import RaceState as LegacyRS
        races[race_id] = LegacyRS()
        ws_connections[race_id] = []
        paused[race_id] = False
        background_tasks.add_task(race_loop, race_id)
        return {"race_id": race_id, "state": races[race_id].to_dict()}


@app.post("/race/{race_id}/tick")
async def manual_tick(race_id: str):
    """Manually advance one lap (for testing or when auto-loop isn't running)."""
    if race_id not in races:
        raise HTTPException(404, "Race not found")
    rs = races[race_id]
    if NEW_SIM:
        if rs.finished:
            return {"state": race_state_to_dict(rs)}
        events = tick_lap(rs)
        new_advice = run_advice_engine(rs)
        if rs.finished and rs.race_summary is None:
            rs.race_summary = build_summary(rs)
        state = race_state_to_dict(rs)
        await broadcast(race_id, {"type": "tick", "state": state, "new_advice": new_advice})
        return {"state": state, "events": events, "new_advice": new_advice}
    else:
        rs.tick()
        state = rs.to_dict()
        await broadcast(race_id, {"type": "tick", "state": state})
        return {"state": state}


@app.post("/race/{race_id}/pit")
async def pit_stop(race_id: str, compound: str = Query("Medium")):
    if race_id not in races:
        raise HTTPException(404, "Race not found")
    rs = races[race_id]

    if NEW_SIM:
        # Normalize compound capitalization
        compound_map = {
            "soft": "Soft", "medium": "Medium", "hard": "Hard",
            "inter": "Inter", "wet": "Wet",
            "Soft": "Soft", "Medium": "Medium", "Hard": "Hard",
            "Inter": "Inter", "Wet": "Wet",
        }
        norm_compound = compound_map.get(compound, "Medium")
        result = execute_player_pit(rs, norm_compound)
        state = race_state_to_dict(rs)
        await broadcast(race_id, {"type": "tick", "state": state})
        return {"status": "pitted", "result": result, "state": state}
    else:
        rs.pit(compound.lower())
        state = rs.to_dict()
        await broadcast(race_id, {"type": "tick", "state": state})
        return {"status": "pitting", "state": state}


@app.post("/race/{race_id}/ers")
async def set_ers(race_id: str, mode: str = Query("balanced")):
    if race_id not in races:
        raise HTTPException(404, "Race not found")
    rs = races[race_id]
    if NEW_SIM:
        mode_map = {
            "harvest": "harvest", "balanced": "balanced",
            "attack": "attack", "overtake": "overtake",
        }
        valid_mode = mode_map.get(mode.lower(), "balanced")
        rs.player_ers_mode = valid_mode
        return {"status": "ok", "mode": valid_mode}
    else:
        rs.set_ers(mode.lower())
        return {"status": "ok", "mode": mode}


@app.post("/race/{race_id}/pause")
async def pause_race(race_id: str):
    if race_id not in races:
        raise HTTPException(404, "Race not found")
    paused[race_id] = True
    return {"status": "paused"}


@app.post("/race/{race_id}/resume")
async def resume_race(race_id: str):
    if race_id not in races:
        raise HTTPException(404, "Race not found")
    paused[race_id] = False
    return {"status": "resumed"}


@app.get("/race/{race_id}/field")
async def get_field(race_id: str):
    """All 20 car states and gaps."""
    if race_id not in races:
        raise HTTPException(404, "Race not found")
    rs = races[race_id]
    if NEW_SIM:
        state = race_state_to_dict(rs)
        return {
            "lap": rs.current_lap,
            "standings": state["standings"],
            "sc_active": rs.sc_active,
            "vsc_active": rs.vsc_active,
        }
    else:
        s = rs.to_dict()
        return {"standings": s.get("standings", []), "lap": s.get("lap", 0)}


@app.get("/race/{race_id}/advice")
async def get_advice_log(race_id: str):
    """Full advice log for this race."""
    if race_id not in races:
        raise HTTPException(404, "Race not found")
    rs = races[race_id]
    if NEW_SIM:
        return {
            "total_advice": len(rs.agent_advice_log),
            "followed": rs.advice_followed_count,
            "ignored": rs.advice_ignored_count,
            "log": rs.agent_advice_log,
        }
    return {"log": [], "total_advice": 0}


@app.get("/race/{race_id}/summary")
async def get_summary(race_id: str):
    if race_id not in races:
        raise HTTPException(404, "Race not found")
    rs = races[race_id]
    if NEW_SIM:
        if not rs.finished:
            raise HTTPException(400, "Race not finished yet")
        if rs.race_summary is None:
            rs.race_summary = build_summary(rs)
        return rs.race_summary
    else:
        if not rs.finished:
            raise HTTPException(400, "Race not finished yet")
        return rs.race_summary or {"error": "No summary available"}


@app.post("/race/{race_id}/acknowledge_advice")
async def acknowledge_advice(race_id: str):
    """Mark current pending advice as acknowledged (starts follow tracking)."""
    if race_id not in races:
        raise HTTPException(404, "Race not found")
    rs = races[race_id]
    if NEW_SIM:
        # Find most recent unresolved advice and mark start of follow window
        for entry in reversed(rs.agent_advice_log):
            if entry.get("followed") is None:
                entry["acknowledged_lap"] = rs.current_lap
                return {"status": "acknowledged", "advice": entry}
        return {"status": "no_pending_advice"}
    return {"status": "ok"}


# ─── WEBSOCKET ────────────────────────────────────────────────────────────────

@app.websocket("/race/{race_id}/live")
async def websocket_endpoint(websocket: WebSocket, race_id: str):
    await websocket.accept()
    if race_id not in ws_connections:
        ws_connections[race_id] = []
    ws_connections[race_id].append(websocket)

    try:
        rs = races.get(race_id)
        if rs:
            if NEW_SIM:
                initial = race_state_to_dict(rs)
            else:
                initial = rs.to_dict()
            await websocket.send_text(json.dumps({
                "type": "connected",
                "state": initial,
            }))
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        if race_id in ws_connections and websocket in ws_connections[race_id]:
            ws_connections[race_id].remove(websocket)


# ─── SSE DEBATE STREAM ───────────────────────────────────────────────────────

AGENT_META = [
    ("engineer_rec", "Race Engineer",   "🔧"),
    ("tyre_rec",     "Tyre Strategist", "🏎"),
    ("weather_rec",  "Race Director",   "📡"),
    ("rival_rec",    "Field Analyst",   "👁"),
]


async def sse_debate_generator(race_id: str):
    if race_id not in races:
        return
    try:
        rs = races[race_id]
        if NEW_SIM:
            race_data = race_state_to_dict(rs)
            # Enrich with fields the old debate orchestrator expects
            race_data["lap"] = rs.current_lap
            race_data["laps_remaining"] = rs.total_laps - rs.current_lap
            race_data["player"] = race_data.get("player", {})
            race_data["analysis"] = race_data.get("analysis", {})
            race_data["weather"] = {"state": rs.weather, "rain_prob_next_10": 0.05}
            race_data["track_temp_c"] = rs.track_temp
        else:
            race_data = rs.to_dict()

        result = run_debate(race_data)

        # Parse recommended pit lap from LLM response
        try:
            import re
            decision_text = result.get("final_decision", "")
            lap_match = re.search(r'lap (\d+)', decision_text.lower())
            if lap_match and race_id in races:
                recommended_lap = int(lap_match.group(1))
                if NEW_SIM:
                    races[race_id].last_recommendation_lap = recommended_lap
                    races[race_id].last_recommendation_action = "PIT_NOW"
                else:
                    races[race_id].set_recommended_pit_lap(recommended_lap)
        except Exception:
            pass

        for key, label, icon in AGENT_META:
            text = result.get(key, "Analysis complete.")
            yield f"data: {json.dumps({'type': 'agent_start', 'agent': label, 'icon': icon})}\n\n"
            for word in str(text).split():
                yield f"data: {json.dumps({'type': 'token', 'agent': label, 'token': word + ' '})}\n\n"
                await asyncio.sleep(0.02)
            yield f"data: {json.dumps({'type': 'agent_done', 'agent': label})}\n\n"

        yield f"data: {json.dumps({'type': 'summary', 'decision': result.get('final_decision'), 'radio': result.get('radio_message')})}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"


@app.get("/race/{race_id}/stream")
async def stream_debate(race_id: str):
    return StreamingResponse(sse_debate_generator(race_id), media_type="text/event-stream")


# ─── LIBRARY STATUS ──────────────────────────────────────────────────────────

@app.get("/library/status")
async def library_status():
    """Check if race_library.json is built and ready."""
    if not NEW_SIM:
        return {"new_sim": False, "message": "Running legacy simulation"}
    try:
        lib = load_library()
        circuits = list({s["circuit"] for s in lib})
        return {
            "new_sim": True,
            "ready": True,
            "race_count": len(lib),
            "circuits": circuits,
        }
    except FileNotFoundError:
        return {
            "new_sim": True,
            "ready": False,
            "message": "Run: python -m backend_pitstop.data.race_library build",
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)