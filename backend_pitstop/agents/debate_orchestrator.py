from langgraph.graph import StateGraph, END
from typing import TypedDict, List
from agents.race_engineer import race_engineer_agent
from agents.tyre_strategist import tyre_strategist_agent
from agents.weather_oracle import weather_oracle_agent
from agents.rival_analyst import rival_analyst_agent
from rag.retriever import get_strategy_context
from groq import Groq
import os

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
    state["engineer_rec"] = race_engineer_agent(
        state["race_state"], state["rag_context"])
    return state

def tyre_node(state: RaceDebateState) -> RaceDebateState:
    state["tyre_rec"] = tyre_strategist_agent(
        state["race_state"], state["rag_context"])
    return state

def weather_node(state: RaceDebateState) -> RaceDebateState:
    state["weather_rec"] = weather_oracle_agent(
        state["race_state"], state["rag_context"])
    return state

def rival_node(state: RaceDebateState) -> RaceDebateState:
    state["rival_rec"] = rival_analyst_agent(
        state["race_state"], state["rag_context"])
    return state

def synthesiser_node(state: RaceDebateState) -> RaceDebateState:
    prompt = f"""You are the Pit Wall Director.
Four specialists have given their recommendations:
Race Engineer: {state['engineer_rec']}
Tyre Strategist: {state['tyre_rec']}
Weather Oracle: {state['weather_rec']}
Rival Analyst: {state['rival_rec']}
Synthesise these into ONE final strategy call.
FINAL DECISION: [the action to take]
CONFIDENCE: [HIGH if all agree / MEDIUM if 3 agree / LOW if split]
SUMMARY: [2 sentences explaining the consensus]"""
    r = groq_client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[{"role":"user","content":prompt}],
        max_tokens=250)
    output = r.choices[0].message.content
    state["final_decision"] = output
    highs = sum(1 for rec in [state['engineer_rec'], state['tyre_rec'],
                               state['weather_rec'], state['rival_rec']]
                if "CONFIDENCE: HIGH" in rec)
    state["confidence"] = "HIGH" if highs >= 3 else "MEDIUM" if highs >= 2 else "LOW"
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
    rs = race_state
    ctx = get_strategy_context(rs["lap"], rs["compound"],
                               rs["tyre_age"], rs["gap_to_leader"])
    initial = RaceDebateState(
        race_state=rs, rag_context=ctx,
        engineer_rec="", tyre_rec="", weather_rec="",
        rival_rec="", final_decision="", confidence="")
    result = debate_graph.invoke(initial)
    return result