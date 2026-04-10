import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

PROMPT = """You are an F1 Tyre Strategist. Your ONLY job is pit window decisions.
Analyse tyre age and compound. Decide: pit now / extend / stay out.
FORMAT:
RECOMMENDATION: [action]
CONFIDENCE: [HIGH/MEDIUM/LOW]
REASONING: [1-2 sentences]"""

def tyre_strategist_agent(race_state: dict, rag_context: list) -> str:
    context_str = "\n".join(rag_context)
    user_msg = f"State: {race_state}\nContext: {context_str}"
    r = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role":"system","content":PROMPT},{"role":"user","content":user_msg}]
    )
    return r.choices[0].message.content