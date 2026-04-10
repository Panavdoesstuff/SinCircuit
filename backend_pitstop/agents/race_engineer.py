import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv() # Crucial to load your GROQ_API_KEY

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

PROMPT = """You are a senior F1 Race Engineer. Your ONLY job is lap time optimisation.
Given the race state and historical context, analyse lap time trends and pace management.
Respond in EXACTLY this format:
RECOMMENDATION: [one clear action]
CONFIDENCE: [HIGH/MEDIUM/LOW]
REASONING: [2-3 sentences max]
Do not discuss tyres or weather — that is not your role."""

def race_engineer_agent(race_state: dict, rag_context: list) -> str:
    context_str = "\n".join(rag_context)
    user_msg = f"""Current race state:
Lap: {race_state['lap']}/{race_state['total_laps']}
Tyre: {race_state['compound']}, age {race_state['tyre_age']} laps
Gap to leader: {race_state['gap_to_leader']}s
Weather: {race_state['weather']}

Historical similar scenarios:
{context_str}

What is your recommendation?"""
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile", # Use the same model as your others for consistency
        messages=[{"role":"system","content":PROMPT},
                  {"role":"user","content":user_msg}],
        max_tokens=200
    )
    return response.choices[0].message.content