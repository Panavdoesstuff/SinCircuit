import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """You are an F1 Tyre and Track Strategist. You own compound selection, pit timing, and surface state.

Analyse ALL of the following to determine optimal pit strategy:
- Current compound, tyre age, and degradation rate (seconds lost per lap vs baseline).
- Tyre temperature window: are tyres in the optimal operating window? Under or overtemp costs lap time.
- Cliff prediction: at what lap will this tyre hit the performance cliff (sudden 1–2s/lap loss)?
- Track evolution: rubber buildup improves lap times — factor whether staying out benefits from further track improvement.
- Track temperature: higher track temp increases deg rate.
- Safety car / VSC probability: if a safety car is likely in the next 10 laps, pitting under SC would cost only ~5s vs ~22.5s in clean air. Flag this window.
- Overcut feasibility: if rivals pit now and you stay out on fresh track evolution, can you build enough gap to cover their out-lap?
- Undercut feasibility: can a fresh tyre advantage on the out-lap overcome the pit stop time loss?
- Available compounds and FIA two-compound rule: has the rule been satisfied? Flag which compounds remain.
- Historical RAG context: cite the most similar historical scenarios and their outcomes.

Respond in EXACTLY this format — no extra text:
RECOMMENDATION: [pit now / extend X laps / stay out — specific lap number]
CONFIDENCE: [HIGH / MEDIUM / LOW]
CLIFF_LAP: [predicted lap number of performance cliff]
SC_WINDOW: [LOW / MEDIUM / HIGH probability in next 10 laps]
REASONING: [3–4 sentences with specific numbers and historical citations]"""


def tyre_strategist_agent(race_state: dict, rag_context: list) -> str:
    context_str = "\n".join(rag_context) if rag_context else "No historical data."

    undercuts = race_state.get("undercut_threats", [])
    overcuts = race_state.get("overcut_targets", [])

    undercut_str = "\n".join([
        f"  {t['driver']} ({t['constructor']}): {t['gap_behind']}s behind, "
        f"age {t['tyre_age']} laps on {t['compound']}, threat window {t['threat_window_laps']} laps"
        for t in undercuts
    ]) or "  None identified"

    overcut_str = "\n".join([
        f"  {t['driver']} ({t['constructor']}): {t['gap_ahead']}s ahead, "
        f"age {t['tyre_age']} laps on {t['compound']}, window {t['window_laps']} laps"
        for t in overcuts
    ]) or "  None identified"

    user_msg = f"""Tyre and track state — Las Vegas Street Circuit:
Compound: {race_state['compound']}, age {race_state['tyre_age']} laps
Tyre status: {race_state['tyre_status']}
Laps to performance cliff: {race_state['laps_to_cliff']}
Laps remaining: {race_state['laps_remaining']}
Track temp: {race_state['track_temp_c']}°C
Track evolution (rubber buildup benefit): {race_state['track_evolution_s']}s
Safety car active: {race_state['safety_car_active']}
Pit lane delta at Las Vegas: {race_state['pit_lane_delta_s']}s
Used compounds: {race_state['used_compounds']}
Two-compound rule satisfied: {race_state['two_compound_rule_satisfied']}

Undercut threats (cars behind, older tyres):
{undercut_str}

Overcut opportunities (cars ahead, older tyres):
{overcut_str}

Historical similar scenarios:
{context_str}

What is your pit strategy recommendation?"""

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