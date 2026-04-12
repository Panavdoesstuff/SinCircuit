import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Initialize the client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def get_agent_response(role, situation, context):
    """
    Sends the race context to Groq and returns the agent's response.
    """
    prompts = {
        "strategist": "You are a cutthroat F1 Strategist. Prioritize speed and aggression.",
        "specialist": "You are a Tyre Specialist. You are conservative and worry about wear.",
        "engineer": "You are the Head Race Engineer. Listen to the debate and make a final call."
    }
    
    # Simple check to ensure role exists
    system_prompt = prompts.get(role, "You are an F1 expert.")

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"HISTORICAL CONTEXT:\n{context}\n\nCURRENT SITUATION:\n{situation}"}
            ],
            model="llama-3.3-70b-versatile",
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"Agent Error: {str(e)}"