
import os
import json
from groq import Groq
from rag.retriever import get_strategy_context
from knowledge_base import query_strategy_logic

# Initialize Groq
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def run_debate(race_data: dict):
    """
    Orchestrates a detailed F1 pit wall debate using Llama 3 and RAG context.
    """
    # ─── DATA EXTRACTION ───
    lap = race_data.get("lap", 1)
    player = race_data.get("player", {})
    analysis = race_data.get("analysis", {})
    weather_data = race_data.get("weather", {})
    
    compound = player.get("compound", "medium")
    tyre_age = player.get("tyre_age", 0)
    pos = analysis.get("player_position", "P1")
    gap = analysis.get("gap_to_leader_s", 0.0)
    laps_rem = race_data.get("laps_remaining", 50)
    weather = weather_data.get("state", "dry")
    track_temp = race_data.get("track_temp_c", 38.0)
    
    # ─── STEP 1: RETRIEVE HISTORICAL CONTEXT (RAG) ───
    rag_context = get_strategy_context(
        lap=lap, 
        compound=compound, 
        tyre_age=tyre_age, 
        gap=gap, 
        laps_remaining=laps_rem,
        weather=weather
    )
    history_str = "\n".join(rag_context)

    # ─── STEP 2: MULTI-AGENT PROMPT ───
    system_prompt = f"""
    You are an F1 Strategy Orchestrator. You are managing a race for 'Panav' who is currently {pos}.
    You must generate a structured debate between four specialists. 
    
    CURRENT TELEMETRY:
    - Position: {pos} | Lap: {lap} | Remaining: {laps_rem}
    - Tyres: {compound} ({tyre_age} laps old)
    - Weather: {weather} | Track Temp: {track_temp}°C
    
    HISTORICAL RAG DATA:
    {history_str}

    INSTRUCTIONS:
    1. Respond ONLY in a valid JSON format.
    2. Provide detailed, technical reasoning (3-4 sentences each).
    3. Use the RAG data to justify decisions (e.g., 'Similar to Hamilton in 2021...').
    4. The 'radio_message' should be punchy and professional.
    """

    user_prompt = """
    Please provide the following JSON keys:
    'engineer_rec': Focus on engine/ERS and gaps.
    'tyre_rec': Focus on degradation and the 'cliff'.
    'weather_rec': Focus on rain probability and track temp.
    'rival_rec': Focus on what VER/LEC are doing.
    'final_decision': 'BOX' or 'STAY OUT'.
    'radio_message': A short message to the driver.
    """

    # ─── STEP 3: CALL LLM ───
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"} # Forces JSON output
        )
        
        # Parse the JSON response from the LLM
        ai_output = json.loads(chat_completion.choices[0].message.content)
        
        # ─── STEP 4: RETURN DYNAMIC RESULT ───
        return {
            "engineer_rec": ai_output.get("engineer_rec", "Keep pushing."),
            "tyre_rec": ai_output.get("tyre_rec", "Monitor the fronts."),
            "weather_rec": ai_output.get("weather_rec", "Radar is clear."),
            "rival_rec": ai_output.get("rival_rec", "Verstappen is within DRS."),
            "final_decision": ai_output.get("final_decision", "STAY OUT"),
            "dominant_factor": "Race Pace",
            "confidence": 0.9,
            "risk": "Moderate",
            "contingency": "Prepare for a safety car restart.",
            "radio_message": ai_output.get("radio_message", "Push now, Panav."),
            "rag_context": history_str
        }
        
    except Exception as e:
        print(f"Error in LLM debate: {e}")
        # Fallback to keep the app running if API fails
        return {
            "engineer_rec": "Telemetry data error. Reverting to base strategy.",
            "tyre_rec": "Check tyre pressures manually.",
            "weather_rec": "Visual confirmation of dry track.",
            "rival_rec": "Maintain gap to car behind.",
            "final_decision": "STAY OUT",
            "radio_message": "Radio check, Panav. Stay focused.",
            "rag_context": "None"
        }

        