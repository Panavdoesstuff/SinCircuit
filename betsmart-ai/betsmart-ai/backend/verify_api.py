import os
import sys
# Add current and parent dir to path to help with imports
sys.path.append(os.getcwd())
from services.odds_fetcher import get_live_odds, API_KEY

print(f"Testing Odds API with KEY: {API_KEY[:5]}...")
try:
    data = get_live_odds("upcoming")
    print(f"Success! Found {len(data)} matches.")
    if data:
        print(f"First match: {data[0].get('home_team')} vs {data[0].get('away_team')}")
        from services.arbitrage import find_arbitrage
        from services.odds_fetcher import get_best_odds
        best = get_best_odds(data)
        arbs = find_arbitrage(best)
        print(f"Found {len(arbs)} arbitrage opportunities.")
except Exception as e:
    print(f"Test failed: {e}")
