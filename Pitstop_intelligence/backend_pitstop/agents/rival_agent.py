import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """You are an F1 Field Analyst. You monitor all 19 rival cars and identify strategic threats and opportunities.
Analyse ALL of the following:
- Current running order: positions, gaps, and tyre states of all nearby rivals.
- Undercut threats: cars behind on older tyres who could pit, gain time on fresh rubber, and emerge ahead.
- Overcut opportunities: cars ahead on older tyres you can stay out against and emerge ahead after they pit.
- DRS train: 3+ cars within 1s of each other.
- Historical context: Use provided RAG data to see how similar historical gaps were handled.

Respond in EXACTLY this format — no extra text:
RECOMMENDATION: [the strategic action implied by field state]
CONFIDENCE: [HIGH / MEDIUM / LOW]
UNDERCUT_THREAT: [driver name and threat window in laps, or NONE]
OVERCUT_TARGET: [driver name and opportunity window, or NONE]
DRS_SITUATION: [description of DRS availability and any train risk]
REASONING: [3–4 sentences with specific driver references, gap numbers, and tyre states]"""

def rival_analyst_agent(race_state: dict, rag_context: list) -> str:
    # 1. Extract and format the field data safely
    field = race_state.get("field", [])
    undercuts = race_state.get("undercut_threats", [])
    overcuts = race_state.get("overcut_targets", [])
    
    # 2. Build detailed field strings for the prompt
    field_str = "\n".join([
        f"  P{c.get('position')} {c.get('driver')} ({c.get('constructor')}): "
        f"{c.get('gap_to_leader')}s from leader, {c.get('compound')} age {c.get('tyre_age')}"
        for c in field
    ]) or "  No field data"

    undercut_str = "\n".join([
        f"  {t.get('driver')}: {t.get('gap_behind')}s behind, {t.get('compound')} age {t.get('tyre_age')}"
        for t in undercuts
    ]) or "  None"

    # 3. Format RAG context so the AI can read it
    history_str = "\n".join(rag_context) if rag_context else "No historical matches."

    user_msg = f"""Full field state — Lap {race_state.get('lap')}/{race_state.get('total_laps')}:
Your gap to leader: {race_state.get('gap_to_leader')}s
Your compound: {race_state.get('compound')}, age {race_state.get('tyre_age')}

Historical Precedents (RAG):
{history_str}

Top 10 rivals by proximity:
{field_str}

Undercut threats (behind you):
{undercut_str}

What is the field-based strategic recommendation?"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg}
        ],
        max_tokens=350,
        temperature=0.3,
    )
    return response.choices[0].message.content