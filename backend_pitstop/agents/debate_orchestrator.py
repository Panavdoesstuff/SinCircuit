from langgraph.graph import StateGraph, END
from typing import TypedDict, List
import os
from groq import Groq
from dotenv import load_dotenv

# Import your specific agent functions
from agents.race_engineer import race_engineer_agent
from agents.tire_agent import tyre_strategist_agent
from agents.weather_agent import weather_oracle_agent
from agents.rival_agent import rival_analyst_agent
from rag.retriever import get_strategy_context

load_dotenv()
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

class RaceDebateState(TypedDict):
    race_state: dict
    rag_context: List[str]
    engineer_rec: str
    tyre_rec: str
    weather_rec: str
    rival_rec: str
    final_decision: str
    confidence: str

def engineer_node(state: RaceDebateState) -> RaceDebateState:
    state["engineer_rec"] = race_engineer_agent(state["race_state"], state["rag_context"])
    return state

def tyre_node(state: RaceDebateState) -> RaceDebateState:
    state["tyre_rec"] = tyre_strategist_agent(state["race_state"], state["rag_context"])
    return state

def weather_node(state: RaceDebateState) -> RaceDebateState:
    state["weather_rec"] = weather_oracle_agent(state["race_state"], state["rag_context"])
    return state

def rival_node(state: RaceDebateState) -> RaceDebateState:
    state["rival_rec"] = rival_analyst_agent(state["race_state"], state["rag_context"])
    return state

def synthesiser_node(state: RaceDebateState) -> RaceDebateState:
    prompt = f"""You are the Pit Wall Director. Synthesise these views:
Engineer: {state['engineer_rec']}
Tyre: {state['tyre_rec']}
Weather: {state['weather_rec']}
Rival: {state['rival_rec']}

Respond in EXACTLY this format:
FINAL DECISION: [The specific action to take]
SUMMARY: [2 sentences max explaining why]"""

    r = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role":"user","content":prompt}]
    )
    state["final_decision"] = r.choices[0].message.content
    
    # Logic: Count how many experts are HIGH confidence
    all_recs = [state['engineer_rec'], state['tyre_rec'], state['weather_rec'], state['rival_rec']]
    high_count = sum(1 for rec in all_recs if "CONFIDENCE: HIGH" in rec)
    state["confidence"] = "HIGH" if high_count >= 3 else "MEDIUM" if high_count >= 2 else "LOW"
    return state

def build_debate_graph():
    g = StateGraph(RaceDebateState)
    g.add_node("engineer", engineer_node)
    g.add_node("tyre", tyre_node)
    g.add_node("weather", weather_node)
    g.add_node("rival", rival_node)
    g.add_node("synthesiser", synthesiser_node)
    
    g.set_entry_point("engineer")
    g.add_edge("engineer", "tyre")
    g.add_edge("tyre", "weather")
    g.add_edge("weather", "rival")
    g.add_edge("rival", "synthesiser")
    g.add_edge("synthesiser", END)
    return g.compile()

debate_graph = build_debate_graph()

def run_debate(race_state: dict) -> dict:
    # Get RAG context once to share across all agents
    ctx = get_strategy_context(
        race_state["lap"], 
        race_state["compound"], 
        race_state["tyre_age"], 
        race_state["gap_to_leader"]
    )
    initial = RaceDebateState(
        race_state=race_state, 
        rag_context=ctx, 
        engineer_rec="", tyre_rec="", weather_rec="", rival_rec="", 
        final_decision="", confidence=""
    )
    return debate_graph.invoke(initial)