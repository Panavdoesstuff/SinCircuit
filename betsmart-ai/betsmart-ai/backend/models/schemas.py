from pydantic import BaseModel
from typing import List, Optional

class ChatMessage(BaseModel):
    role: str          # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = []

class PokerV2Request(BaseModel):
    your_cards: List[str]                        # e.g. ["Ah", "Kd"]
    community_cards: Optional[List[str]] = []    # e.g. ["2h", "7c", "Jd"]
    pot_size: Optional[float] = 100.0
    call_amount: Optional[float] = 20.0
    opponents_total_bet: Optional[float] = 0.0   # total chips pushed in by all opponents
    num_opponents: Optional[int] = 1             # number of active opponents at the table
