import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """You are the F1 Race Director Strategist. You assess macro race conditions and external factors.

Analyse ALL of the following:
- Safety car probability: Las Vegas historically has ~1 SC per race, typically laps 15–40. Is the current lap in the risk window?
- VSC probability: minor incidents, slow cars, debris — assess likelihood in next 5 laps.
- Lap time delta trend: is pace improving (track evolution, fuel burn) or degrading (tyre wear)?
- Circuit overtaking difficulty: Las Vegas Street Circuit has 2 DRS zones, long straights — overtaking rated 7/10 feasibility. Factor this into whether track position or fresh tyres matter more.
- Circuit tyre sensitivity: Las Vegas has high rear deg due to high-speed sweepers — adjust all deg estimates upward.
- Pit lane delta for Las Vegas: ~22.5s time loss. This determines undercut viability window.
- Remaining laps: is a two-stop or one-stop physically executable? Calculate whether fresh tyres reach the end.
- Weather forecast: current conditions and rain probability in next 15 laps. Rain changes every other agent's analysis.
- Championship context: standard points race — balanced risk tolerance.

Respond in EXACTLY this format — no extra text:
RECOMMENDATION: [macro strategic recommendation]
CONFIDENCE: [HIGH / MEDIUM / LOW]
SC_RISK_WINDOW: [current lap range and probability — LOW/MEDIUM/HIGH]
LAPS_REMAINING: [remaining laps and whether another stop is feasible]
WEATHER: [current and 15-lap forecast]
REASONING: [3–4 sentences citing circuit-specific numbers and race context]"""


def weather_oracle_agent(race_state: dict, rag_context: list) -> str:
    lap = race_state['lap']
    total = race_state['total_laps']
    remaining = race_state['laps_remaining']

    # Rough SC risk window for Las Vegas
    sc_risk = "HIGH" if 15 <= lap <= 40 else "LOW"
    one_stop_viable = remaining <= 30
    two_stop_viable = remaining >= 20

    user_msg = f"""Macro race state — Las Vegas Street Circuit:
Current lap: {lap}/{total} ({remaining} laps remaining)
Weather: {race_state['weather']}
Track temp: {race_state['track_temp_c']}°C
Track evolution: {race_state['track_evolution_s']}s accumulated
Safety car active RIGHT NOW: {race_state['safety_car_active']}
SC laps remaining: {race_state['sc_laps_remaining']}
Lap time trend (last 5 laps): {race_state.get('lap_time_trend', [])}

Circuit context:
- Pit lane delta: {race_state['pit_lane_delta_s']}s
- DRS zones: {race_state['drs_zones']}
- Overtaking difficulty: {race_state['overtaking_difficulty']}
- Tyre sensitivity: {race_state['circuit_tyre_sensitivity']}

SC risk window assessment: {sc_risk} (lap {lap} in {'prime' if 15<=lap<=40 else 'low'} SC window)
One-stop viable from here: {one_stop_viable}
Two-stop viable from here: {two_stop_viable}

What is your macro strategic recommendation?"""

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