import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

PROMPT = """You are an F1 Weather Analyst. Your ONLY job is rain risk assessment.
FORMAT:
RECOMMENDATION: [stay on slicks / prepare inters / pit for wets]
CONFIDENCE: [HIGH/MEDIUM/LOW]
REASONING: [1-2 sentences]"""

def weather_oracle_agent(race_state: dict, rag_context: list) -> str:
    user_msg = f"Weather: {race_state['weather']}, Lap: {race_state['lap']}"
    r = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role":"system","content":PROMPT},{"role":"user","content":user_msg}]
    )
    return r.choices[0].message.content