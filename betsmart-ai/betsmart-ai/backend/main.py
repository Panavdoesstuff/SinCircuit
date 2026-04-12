from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import logging
import asyncio
from datetime import datetime

import os
from dotenv import load_dotenv
load_dotenv()

# Custom imports
try:
    from services.odds_fetcher import get_live_odds, get_best_odds, get_mock_odds, get_all_active_odds
    from services.arbitrage import find_arbitrage, stake_distribution, get_bookmaker_link
    from services.decision_engine import analyze_event
    from services.casino import blackjack_advice, poker_advice, poker_advice_v2
    from services.sports_genres import SPORTS_GENRES
    from agents.llm_engine import generate_ai_response, chat_with_strategist, groq_search_answer, is_sports_betting_query
except ImportError as e:
    print(f"CRITICAL ERROR: Missing a file! {e}")
app = FastAPI()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
#  Search Index & Background Worker
# ─────────────────────────────────────────────

from models.schemas import *

class SearchIndex:
    def __init__(self):
        self.matches = []
        self.teams = set()
        self.last_updated = None
        self.is_warming_up = True

    def update(self, new_matches):
        self.matches = new_matches
        new_teams = set()
        for m in self.matches:
            new_teams.add(m.get('home_team', ''))
            new_teams.add(m.get('away_team', ''))
        self.teams = new_teams
        self.last_updated = datetime.now()
        self.is_warming_up = False

global_index = SearchIndex()

async def background_indexer():
    while True:
        try:
            logger.info('Background Indexer: Refreshing search database...')
            all_data = await asyncio.to_thread(get_all_active_odds)
            if all_data:
                global_index.update(all_data)
                logger.info(f'Background Indexer: Successfully indexed {len(all_data)} matches.')
            else:
                logger.warn('Background Indexer: No data fetched, keeping old index.')
        except Exception as e:
            logger.error(f'Background Indexer Error: {e}')
        await asyncio.sleep(900)

@app.on_event('startup')
async def startup_event():
    asyncio.create_task(background_indexer())



@app.get("/health")
def health_check():
    """Health check endpoint for deployment probes."""
    logger.info("Health check ping received.")
    return {"status": "online", "version": "1.0.0", "multi_agent": "enabled"}

# ─────────────────────────────────────────────
#  Existing endpoints
# ─────────────────────────────────────────────

@app.get("/full-system")
def full_system():
    try:
        from agents.coordinator import orchestrate_analysis
        logger.info("Triggering Multi-Agent Orchestrator (Scout -> Analyst -> Critic)")
        return orchestrate_analysis()

    except Exception as e:
        logger.error(f"Backend Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/search")
def search(q: str):
    try:
        query = q.strip()
        if not query:
            return {"results": [], "query": q, "status": "empty", "ai_answer": None, "is_betting_related": True}

        logger.info(f"AI Search Query received: '{query}'")

        # 1. Use the pre-indexed data (Instant!)
        data = global_index.matches
        if not data:
            # Force real API data fetching instead of mocking
            logger.info("Search index not ready yet, fetching live odds directly from API...")
            data = get_live_odds("upcoming") 

        # 2. Build best-odds pool
        best_data = get_best_odds(data)

        # 3. Get AI intent analysis (Groq) — pass match context
        match_context = [{"match": m["match"], "genre": m.get("genre", "")} for m in best_data[:12]]
        ai_result = groq_search_answer(query, match_context)

        # 4. If NOT a betting/sports query — return no-results immediately
        if not ai_result.get("is_betting_related", True):
            return {
                "query": q,
                "matches": [],
                "sites": [],
                "genres": [],
                "ai_answer": None,
                "is_betting_related": False,
                "status": "not_betting_related",
                "last_updated": global_index.last_updated
            }

        # 5. Search matches — use AI-extracted team/sport for smarter matching
        query_lower = query.lower()
        extracted_team = (ai_result.get("extracted_team") or "").lower()
        extracted_sport = (ai_result.get("extracted_sport") or "").lower()

        match_results = []
        for match in best_data:
            match_name = match["match"].lower()
            genre = match.get("genre", "").lower()
            bookmakers = [o["book"].lower() for o in match["best_odds"]]

            # Multi-signal scoring
            score = 0
            query_words = query_lower.split()
            for word in query_words:
                if len(word) < 2:
                    continue
                if word in match_name:
                    score += 3
                if word in genre:
                    score += 2
                if any(word in b for b in bookmakers):
                    score += 1

            # Boost score if extracted info matches
            if extracted_team and extracted_team in match_name:
                score += 5
            if extracted_sport and extracted_sport in genre:
                score += 4
            # Partial word match for team names (e.g. "Real" -> "Real Madrid")
            for part in query_lower.split():
                if len(part) >= 4 and part in match_name:
                    score += 2

            if score >= 2:
                analysis = analyze_event(match)
                enriched_odds = []
                for o in match["best_odds"]:
                    info = get_bookmaker_link(o["book"])
                    enriched_odds.append({**o, "link": info["url"], "region_locked": info["region_locked"]})

                ev_val = 0
                if analysis:
                    ev_val = analysis[0]["analysis"]["math"]["ev"]

                match_results.append({
                    "type": "match",
                    "match": match["match"],
                    "genre": match.get("genre", "Unknown"),
                    "best_odds": enriched_odds,
                    "analysis": analysis[0]["analysis"] if analysis else None,
                    "_score": score,
                    "_ev": ev_val
                })

        # Sort: by EV descending (value first), then by relevance score
        match_results.sort(key=lambda x: (x["_ev"], x["_score"]), reverse=True)
        # Clean internal sort keys
        for m in match_results:
            m.pop("_score", None)
            m.pop("_ev", None)

        # 6. Search genres & sites
        site_results = []
        genre_results = []
        for genre_obj in SPORTS_GENRES:
            g_name = genre_obj["genre"].lower()
            sports_lower = [s.lower() for s in genre_obj["sports"]]

            genre_match = (
                query_lower in g_name or
                any(query_lower in s for s in sports_lower) or
                (extracted_sport and extracted_sport in g_name) or
                any(word in g_name for word in query_lower.split() if len(word) >= 3)
            )

            if genre_match:
                genre_results.append({
                    "type": "genre",
                    "name": genre_obj["genre"],
                    "icon": genre_obj["icon"],
                    "best_sites": genre_obj["best_sites"][:3]
                })

            for site in genre_obj["best_sites"]:
                site_name = site["name"].lower()
                if query_lower in site_name or any(word in site_name for word in query_lower.split() if len(word) >= 4):
                    site_results.append({
                        "type": "site",
                        "name": site["name"],
                        "url": site["url"],
                        "reason": site["reason"],
                        "bonus": site["bonus"],
                        "pro_tip": site.get("pro_tip", ""),
                        "genre_context": genre_obj["genre"]
                    })

        # Deduplicate sites
        seen_sites: set = set()
        unique_sites = []
        for s in site_results:
            if s["name"] not in seen_sites:
                unique_sites.append(s)
                seen_sites.add(s["name"])

        return {
            "query": q,
            "matches": match_results[:15],
            "sites": unique_sites[:6],
            "genres": genre_results[:4],
            "ai_answer": ai_result.get("answer", ""),
            "is_betting_related": True,
            "intent": ai_result.get("intent", "general"),
            "status": "ready" if not global_index.is_warming_up else "warming_up",
            "last_updated": global_index.last_updated
        }
    except Exception as e:
        logger.error(f"Search Engine Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/suggestions")
def suggestions(q: str):
    try:
        query = q.lower().strip()
        if not query: return {"suggestions": []}
        
        # Use indexed teams and categories for instant suggestions
        suggestion_set = set()
        
        # 1. Teams from Index
        for team in global_index.teams:
            if query in team.lower():
                suggestion_set.add(team)
        
        # 2. Genres & Leagues
        for g in SPORTS_GENRES:
            if query in g["genre"].lower(): suggestion_set.add(g["genre"])
            for s in g["sports"]:
                if query in s.lower(): suggestion_set.add(s)
        
        # If index is empty, fetch a quick live batch for suggestions
        if not suggestion_set and global_index.is_warming_up:
            live_batch = get_live_odds("upcoming")
            if live_batch:
                for match in live_batch:
                    if query in match.get("home_team", "").lower(): suggestion_set.add(match.get("home_team", ""))
                    if query in match.get("away_team", "").lower(): suggestion_set.add(match.get("away_team", ""))

        return {"suggestions": sorted(list(suggestion_set))[:10]}
    except Exception as e:
        logger.error(f"Suggestions Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/blackjack")
def blackjack(player_total: int, dealer_card: int):
    return {"decision": blackjack_advice(player_total, dealer_card)}


@app.get("/poker")
def poker(hand_strength: float, pot_odds: float):
    return {"decision": poker_advice(hand_strength, pot_odds)}


# ─────────────────────────────────────────────
#  AI Strategist Chat
# ─────────────────────────────────────────────

@app.post("/chat")
def chat(req: ChatRequest):
    try:
        history = [{"role": m.role, "content": m.content} for m in req.history]
        reply   = chat_with_strategist(history, req.message)
        return {"reply": reply}
    except Exception as e:
        logger.error(f"Chat Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────
#  Poker v2 — Real card inputs + opponent data
# ─────────────────────────────────────────────

@app.post("/poker-v2")
def poker_v2(req: PokerV2Request):
    try:
        result = poker_advice_v2(
            your_cards          = req.your_cards,
            community_cards     = req.community_cards,
            pot_size            = req.pot_size,
            call_amount         = req.call_amount,
            opponents_total_bet = req.opponents_total_bet,
            num_opponents       = req.num_opponents,
        )
        return result
    except Exception as e:
        logger.error(f"Poker v2 Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────
#  Sports Genres + Best Betting Sites
# ─────────────────────────────────────────────

@app.get("/sports-by-genre")
def sports_by_genre():
    return {"genres": SPORTS_GENRES}


# ─────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
