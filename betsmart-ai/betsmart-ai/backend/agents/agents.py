from utils.vector_store import query_knowledge
from agents.llm_engine import generate_ai_response

def probability_agent(data):
    knowledge = query_knowledge("expected value probability betting")
    return generate_ai_response(data, knowledge)

def risk_agent(data):
    knowledge = query_knowledge("variance risk gambling")
    return generate_ai_response(data, knowledge)

def strategy_agent(data):
    knowledge = query_knowledge("optimal betting strategy kelly")
    return generate_ai_response(data, knowledge)

def run_agents(data):
    return {
        "probability_analysis": probability_agent(data),
        "risk_analysis": risk_agent(data),
        "strategy": strategy_agent(data)
    }