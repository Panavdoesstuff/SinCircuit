import os
import json
from dotenv import load_dotenv
# Load .env if present
# Load .env from the parent directory
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

from core.prompts import SYSTEM_PROMPT, SEARCH_ENGINE_PROMPT, EXPERT_BETTING_ANALYST_PROMPT

try:
    from groq import Groq

    _api_key = os.environ.get("GROQ_API_KEY", "YOUR_GROQ_API_KEY")
    client = Groq(api_key=_api_key)
    USE_LLM = (_api_key != "YOUR_GROQ_API_KEY" and len(_api_key) > 10)
except Exception:
    USE_LLM = False
    client = None


# ─────────────────────────────────────────────────────────────────────────────
#  ORIGINAL — used by agents.py (kept as-is)
# ─────────────────────────────────────────────────────────────────────────────
def generate_ai_response(context, knowledge=None):
    """Original function used by the analysis pipeline."""
    if not USE_LLM:
        return fallback_response(context)

    try:
        prompt = EXPERT_BETTING_ANALYST_PROMPT.format(
            ev=context['ev'],
            variance=context['variance'],
            kelly=context['kelly'],
            edge=context['edge'],
            decision=context['decision'],
            sim_expected_return=context['simulation']['expected_return'],
            sim_max=context['simulation']['max'],
            sim_min=context['simulation']['min']
        )
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()

    except Exception:
        return fallback_response(context)


def fallback_response(context):
    ev       = context["ev"]
    edge     = context["edge"]
    decision = context["decision"]

    edge_text    = "Positive edge suggests market inefficiency." if edge > 0 else "Negative edge suggests no betting advantage."
    decision_text = (
        "This is a high-confidence opportunity."      if decision == "STRONG BET" else
        "This is a moderate opportunity with some risk." if decision == "BET"      else
        "This bet is not favorable."
    )

    return (
        f"Decision: {decision}. "
        f"EV: {ev:.4f}, Edge: {edge:.4f}. "
        f"{edge_text} {decision_text} "
        "Variance indicates potential short-term volatility."
    )


# ─────────────────────────────────────────────────────────────────────────────
#  SEARCH ENGINE — Groq AI-powered sports betting search
# ─────────────────────────────────────────────────────────────────────────────

SPORTS_BETTING_KEYWORDS = [
    # Sports
    "football", "soccer", "basketball", "nba", "nfl", "nhl", "mlb", "cricket",
    "tennis", "mma", "ufc", "boxing", "horse", "racing", "golf", "afl",
    "rugby", "volleyball", "handball", "f1", "formula", "baseball", "hockey",
    # Teams & Tournaments
    "epl", "premier league", "champions league", "la liga", "bundesliga", "serie a",
    "ipl", "bbl", "world cup", "super bowl", "finals", "playoffs", "grand slam",
    # Betting Terms
    "bet", "odds", "wager", "stake", "arbitrage", "arb", "parlay", "moneyline",
    "spread", "handicap", "over", "under", "prop", "accumulator", "acca",
    "value", "ev", "expected value", "kelly", "bankroll", "return", "profit",
    "bookmaker", "sportsbook", "exchange", "betfair", "pinnacle", "draftkings",
    "fanduel", "bet365", "betmgm", "caesars", "bovada", "unibet", "williamhill",
    # Player/Club names (partial)
    "lakers", "celtics", "chiefs", "patriots", "real madrid", "barcelona",
    "liverpool", "manchester", "arsenal", "chelsea", "india", "australia",
    "verstappen", "hamilton", "federer", "djokovic", "nadal", "alcaraz",
]

def is_sports_betting_query(query: str) -> bool:
    """
    Fast keyword-based pre-filter before calling Groq.
    Returns True if the query is likely sports/betting related.
    """
    q = query.lower()
    return any(kw in q for kw in SPORTS_BETTING_KEYWORDS)


def groq_search_answer(query: str, match_context: list = None) -> dict:
    """
    Uses Groq AI to intelligently answer a sports betting search query.
    Returns: { "answer": str, "is_betting_related": bool, "intent": str,
               "extracted_sport": str, "extracted_team": str }
    """
    # First do a fast pre-check
    likely_betting = is_sports_betting_query(query)

    if not USE_LLM:
        # Fallback without Groq
        if likely_betting:
            return {
                "answer": f"Search results for **{query}** — showing matches and bookmakers related to your query.",
                "is_betting_related": True,
                "intent": "general",
                "extracted_sport": "",
                "extracted_team": query
            }
        else:
            return {
                "answer": "",
                "is_betting_related": False,
                "intent": "off_topic",
                "extracted_sport": "",
                "extracted_team": ""
            }
    # Build match context string for AI
    context_str = ""
    if match_context:
        context_str = "\n\nCurrent live/upcoming matches available:\n"
        for m in match_context[:8]:
            context_str += f"- {m.get('match', '')} ({m.get('genre', '')})\n"

    prompt = SEARCH_ENGINE_PROMPT.format(query=query, context_str=context_str)

    try:
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.2,
        )
        raw = response.choices[0].message.content.strip()
        # Clean up markdown code blocks if present
        raw = raw.replace("```json", "").replace("```", "").strip()
        result = json.loads(raw)
        return result
    except Exception as e:
        print(f"Groq search error: {e}")
        # Fallback based on keyword check
        if likely_betting:
            return {
                "answer": f"Showing best results for **{query}** across all sports and bookmakers.",
                "is_betting_related": True,
                "intent": "general",
                "extracted_sport": "",
                "extracted_team": query
            }
        return {
            "answer": "",
            "is_betting_related": False,
            "intent": "off_topic",
            "extracted_sport": "",
            "extracted_team": ""
        }


# ─────────────────────────────────────────────────────────────────────────────
#  NEW — AI Strategist Chat (multi-turn, gambling-only)
# ─────────────────────────────────────────────────────────────────────────────

# SYSTEM_PROMPT is now imported from prompts.py


def chat_with_strategist(conversation_history: list, user_message: str) -> str:
    """
    Multi-turn AI chat with the betting strategist.

    Parameters
    ----------
    conversation_history : list of {"role": "user"|"assistant", "content": str}
    user_message         : the new user message
    """
    if not USE_LLM:
        return _fallback_chat(user_message)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    # Inject prior turns (cap at last 10 to avoid token bloat)
    for msg in conversation_history[-10:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            max_tokens=600,
            temperature=0.75,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"GROQ API ERROR: {e}")
        return _fallback_chat(user_message)


# ── Smart keyword-based fallback (works with NO API key) ─────────────────────

# Keywords that indicate off-topic (non-gambling) questions
_OFF_TOPIC_KEYWORDS = [
    "recipe", "cook", "food", "movie", "song", "music", "code", "program",
    "python", "javascript", "html", "css", "react", "database", "sql",
    "politics", "election", "government", "president", "war", "news",
    "relationship", "love", "dating", "marriage", "health", "medical",
    "doctor", "disease", "weather", "travel", "hotel", "flight",
    "write essay", "essay", "poem", "translate", "language", "history lesson"
]

_GAMBLING_KEYWORDS = [
    "bet", "odds", "gambling", "poker", "blackjack", "casino", "sports",
    "kelly", "ev", "expected value", "bankroll", "stake", "parlay",
    "spread", "moneyline", "arbitrage", "arb", "equity", "pot", "hand",
    "fold", "call", "raise", "check", "bluff", "cricket", "football",
    "soccer", "basketball", "tennis", "horse", "racing", "mma", "ufc",
    "boxing", "ipl", "nba", "nfl", "epl", "variance", "edge", "value",
    "line", "book", "bookmaker", "exchange", "betfair", "pinnacle", "win",
    "lose", "profit", "loss", "card", "deck", "shuffle", "dealer", "house",
    "slot", "roulette", "dice", "baccarat", "sic bo", "keno", "lottery",
    "coinflip", "coin", "flip", "probability", "math", "chance", "random"
]

_FALLBACK_RULES = [
    (
        ["kelly", "bet size", "sizing", "bankroll", "stack"],
        "Kelly Criterion is your sizing bible. The formula is: f = (bp - q) / b, "
        "where b = decimal odds - 1, p = estimated win probability, q = 1 - p. "
        "For example, at 2.0 odds with a 55% edge: f = (1×0.55 - 0.45)/1 = 10% of your bankroll. "
        "In practice, use half-Kelly (5%) to reduce variance without sacrificing much EV. "
        "Actionable tip: never bet more than 5% of your total bankroll on any single event, regardless of edge."
    ),
    (
        ["arbitrage", "arb", "surebet", "guaranteed"],
        "Arbitrage (arb) betting locks in a profit regardless of outcome by exploiting odds gaps between bookmakers. "
        "If Book A offers Team A at 2.10 and Book B offers Team B at 2.05, your arb margin = (1/2.10 + 1/2.05) = 0.963 — a 3.7% guaranteed profit. "
        "Stake proportionally: Stake_A = Total × (1/2.10)/0.963, Stake_B = Total × (1/2.05)/0.963. "
        "Warning: books will limit winning arb accounts fast. Rotate accounts and stay under radar with round numbers. "
        "Actionable tip: use OddsPortal or RebelBetting to find live arb opportunities across 50+ bookmakers instantly."
    ),
    (
        ["poker", "fold", "call", "raise", "hand", "pot odds", "equity", "bluff"],
        "Pot odds are everything in poker. If there's ₹300 in the pot and you face a ₹100 call, your pot odds are 100/400 = 25%. "
        "You need at least 25% equity to make a profitable call. With a flush draw you have ~36% equity (9 outs × 4 = 36 on the flop) — clear call. "
        "As for bluffing: your bluff frequency should match your bet sizing. A half-pot bet needs to work 33% of the time to be profitable. "
        "Actionable tip: always compare your hand equity to pot odds BEFORE deciding — emotion is your biggest leak."
    ),
    (
        ["blackjack", "hit", "stand", "double", "split", "card counting"],
        "Basic blackjack strategy reduces the house edge to ~0.5% — anything else and you're giving money away. "
        "Key deviations: always double 11 vs dealer 2–10; never take insurance (it's a sucker bet at 2:1 for a 33% event); "
        "split Aces and 8s always, never split 10s or 5s. Hi-Lo card counting works: +1 for 2–6, 0 for 7–9, -1 for 10–A. "
        "True Count = Running Count / Decks Remaining. Raise bets when True Count > +2. "
        "Actionable tip: master basic strategy perfectly before counting — deviations without the base are more costly than the count is worth."
    ),
    (
        ["cricket", "ipl", "t20", "test", "odi"],
        "Cricket betting value lives in the in-play market. Books are slow to reprice after wickets in T20s — there's typically a 30–60 second window. "
        "For pre-match, toss wins correlate strongly with match wins at certain grounds (Eden Gardens, Wankhede) — factor that into your probability model. "
        "In Test cricket, session betting (runs in morning/afternoon/evening session) is highly priceable with pitch and weather data. "
        "Best books for cricket: Bet365 (live streaming), 10CRIC (widest Indian markets), Betway (sharp T20 lines). "
        "Actionable tip: model toss advantage by venue — at some IPL grounds it adds 8–12% to win probability, but books only price it 3–5%."
    ),
    (
        ["football", "soccer", "epl", "premier league", "champions league", "la liga"],
        "Football value exists but markets are efficient at the top level. Your edge comes from focusing on leagues books pay less attention to. "
        "Asian Handicap betting strips out the draw and cuts the margin from ~5% to ~1–2%. "
        "For EPL, expected goals (xG) models outperform bookmakers on 1X2 markets by ~2.5% over a season. "
        "Sharp money signal: if a line moves from 1.90 to 1.80 without injury news, that's sharp action — follow it. "
        "Actionable tip: use Pinnacle as your price benchmark. Any book offering 0.05+ better odds on any outcome = positive expected value."
    ),
    (
        ["expected value", "ev", "edge", "value bet", "positive ev"],
        "Expected Value (EV) = (Probability × Profit) - ((1 - Probability) × Stake). "
        "If you estimate 60% chance at 2.0 odds on a ₹1,000 bet: EV = (0.60 × 1000) - (0.40 × 1000) = +₹200. "
        "Always bet positive EV over the long run — short-term variance will smooth out after 1,000+ bets. "
        "Finding true probability is the hard part: use closing line value (CLV) as your benchmark. "
        "Actionable tip: track your bets vs closing odds. If you consistently beat the closing line by 2%+, you're long-term profitable regardless of win rate."
    ),
    (
        ["variance", "risk", "streak", "losing", "tilt"],
        "Variance is not your enemy — it's the mechanism that lets +EV bettors profit long-term. "
        "Even with a 5% edge, you can expect 20–30 bet losing streaks over a 500-bet sample. "
        "The fix: size bets correctly (Kelly/half-Kelly) and never chase losses. Tilt is when emotion overrides math — it's the #1 bankroll killer. "
        "Define session stop-losses: if you're down 15% of session bankroll, stop for the day. "
        "Actionable tip: track EV, not results. Your job is to make +EV decisions. Variance handles the rest over enough samples."
    ),
    (
        ["horse", "racing", "betfair", "exchange", "lay"],
        "Horse racing on Betfair Exchange is unique: you can be the bookmaker and LAY a horse (bet on it to lose). "
        "If a 5/1 horse is overbet by the public, lay it — your liability is 5× your stake but you pocket the stake if it loses. "
        "Key strategy: pre-race price moves reveal market information. If a 10/1 horse drifts to 16/1, the market knows something — don't back it. "
        "In-play racing on Betfair: prices crash immediately after stalls open for front-runners — lay the leader at 1.20 and trade out if it holds. "
        "Actionable tip: use the Betfair Steam signal — when 30%+ of exchange money piles on a horse in 10 minutes, that's insider-like sharp money. Follow it."
    ),
    (
        ["mma", "ufc", "boxing", "fight"],
        "MMA and boxing are among the most mispriced markets in betting. Books rely on public perception, not data. "
        "For UFC: wrestlers are systematically undervalued vs strikers because KO finishes are more memorable. Model wrestling takedown defense carefully. "
        "Method-of-victory markets (decision/KO/submission) are soft — books rarely update them with latest training camp news. "
        "Live MMA betting is high-risk but high-reward: odds swing 10x after an early knockdown that doesn't end the fight. "
        "Actionable tip: track UFC fighters' significant strike accuracy and takedown defense — fighters above 55% strike accuracy vs sub-50% defense opponents win ~70% of time."
    ),
    (
        ["basketball", "nba", "ncaa"],
        "NBA totals (over/under) are easier to beat than spreads. Focus on pace of play mismatches and back-to-back fatigue. "
        "Teams on the second night of a back-to-back score 4–6 fewer points on average — books only shade 2–3 points. "
        "Player prop markets are the softest in the NBA — the lines lag injury news by 15–30 minutes. "
        "NCAAF: small-conference games are priced with minimal research. Sharp money and sharp models work best here. "
        "Actionable tip: monitor the injury report at 11:30 AM on game day — impactful player statuses are released then. Be first to bet props."
    ),
]


def _is_off_topic(message: str) -> bool:
    """Check if message is clearly not about gambling."""
    msg_lower = message.lower()
    has_gambling = any(kw in msg_lower for kw in _GAMBLING_KEYWORDS)
    has_off_topic = any(kw in msg_lower for kw in _OFF_TOPIC_KEYWORDS)
    # If it has gambling keywords, it's on-topic regardless
    if has_gambling:
        return False
    # If it has off-topic keywords without gambling context, it's off-topic
    return has_off_topic


def _fallback_chat(user_message: str) -> str:
    """Rule-based fallback when Groq API is unavailable."""
    msg_lower = user_message.lower()

    # Check if off-topic
    if _is_off_topic(user_message):
        topic_words = [kw for kw in _OFF_TOPIC_KEYWORDS if kw in msg_lower]
        topic = topic_words[0] if topic_words else "that topic"
        return (
            f"I'm BetSmart AI — I'm specifically designed for gambling strategy and betting analysis. "
            f"I can't help with {topic}, but I can give you sharp advice on sports betting, poker, blackjack, "
            f"bankroll management, or any other gambling scenario. What would you like to know?"
        )

    for keywords, response in _FALLBACK_RULES:
        if any(kw in msg_lower for kw in keywords):
            return response

    # Generic response
    return (
        "Great question. As a general principle in gambling strategy: always seek positive expected value (EV), "
        "size your bets proportionally to your edge (Kelly Criterion), and treat variance as a long-term friend — "
        "not a short-term enemy. The market is efficient in major leagues but exploitable in niche markets, "
        "live in-play windows, and prop betting. "
        "Could you give me more detail — which sport, game type, or situation are you asking about? "
        "I can give you a much sharper, numbers-driven answer with more context."
    )