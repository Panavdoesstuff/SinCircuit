import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

PROMPT = """You are an F1 Rival Analyst. Your ONLY job is opponent timing analysis.
FORMAT:
RECOMMENDATION: [undercut / overcut / maintain]
CONFIDENCE: [HIGH/MEDIUM/LOW]
REASONING: [1-2 sentences]"""

def rival_analyst_agent(race_state: dict, rag_context: list) -> str:
    user_msg = f"Rivals: {race_state['rival_pit_laps']}, Gap: {race_state['gap_to_leader']}"
    r = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role":"system","content":PROMPT},{"role":"user","content":user_msg}]
    )
    return r.choices[0].message.content