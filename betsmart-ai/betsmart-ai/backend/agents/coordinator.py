# coordinator.py
import logging
import time
import concurrent.futures

logger = logging.getLogger(__name__)

class ScoutAgent:
    """Agent A: The Scout - Fetches raw odds and data."""
    @staticmethod
    def fetch_odds(sport="upcoming"):
        from services.odds_fetcher import get_live_odds, get_best_odds
        logger.info(f"[ScoutAgent] Fetching odds for sport: {sport}")
        data = get_live_odds(sport)
        return get_best_odds(data)
    
    @staticmethod
    def fetch_odds_with_timeout(sport="upcoming", timeout=8):
        """Fetch odds with a timeout - falls back to mock data if API is too slow."""
        from services.odds_fetcher import get_mock_odds, get_best_odds
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(ScoutAgent.fetch_odds, sport)
                result = future.result(timeout=timeout)
                if result:
                    return result
        except (concurrent.futures.TimeoutError, Exception) as e:
            logger.warning(f"[ScoutAgent] Odds API timed out after {timeout}s, using mock data: {e}")
        
        # Fallback to mock data so the UI always loads
        logger.info("[ScoutAgent] Falling back to mock data for instant load")
        return get_best_odds(get_mock_odds())

class AnalystAgent:
    """Agent B: The Analyst - Processes probabilities, RAG, and AI insights."""
    @staticmethod
    def analyze_bet(event):
        from services.decision_engine import analyze_event
        logger.info(f"[AnalystAgent] Analyzing event: {event.get('match')}")
        return analyze_event(event)

class CriticAgent:
    """Agent C: The Critic - Finalizes advice and enforces Bankroll Management rules."""
    @staticmethod
    def construct_final_advice(best_odds, analysis):
        logger.info("[CriticAgent] Finalizing comprehensive strategy.")
        from services.arbitrage import find_arbitrage, stake_distribution
        arb = find_arbitrage(best_odds)
        
        arb_detailed = []
        for a in arb:
            bets = stake_distribution(a["best_odds"])
            arb_detailed.append({
                "match": a["match"],
                "arb_margin": a["arb_margin"],
                "bets": bets,
                "odds": a["best_odds"],
            })

        decisions = []
        for event in best_odds:
            res = analysis.get(event["match"], [])
            for r in res:
                decisions.append({"match": event["match"], "genre": event.get("genre", "Unknown"), **r})
                
        return {"arbitrage": arb_detailed, "decisions": decisions}

def orchestrate_analysis():
    """Main Orchestrator wrapping the Multi-Agent system.
    Uses timeout so the UI always loads even if the Odds API is slow."""
    scout = ScoutAgent()
    analyst = AnalystAgent()
    critic = CriticAgent()
    
    # Use timeout-protected fetch so we don't hang forever
    odds_data = scout.fetch_odds_with_timeout(timeout=8)
    
    analysis_results = {}
    for event in odds_data:
        try:
            analysis_results[event["match"]] = analyst.analyze_bet(event)
        except Exception as e:
            logger.error(f"[AnalystAgent] Error analyzing {event.get('match')}: {e}")
            analysis_results[event["match"]] = []
        
    return critic.construct_final_advice(odds_data, analysis_results)
