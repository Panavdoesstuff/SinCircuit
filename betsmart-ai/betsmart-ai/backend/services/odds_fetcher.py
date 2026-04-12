import os
import time
import requests
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Load .env from the root backend directory
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(env_path)

# Load API key from .env (user's Odds API key)
API_KEY = os.environ.get("ODDS_API_KEY")

if not API_KEY:
    print(f"WARNING: ODDS_API_KEY is not set in environment! Checked: {env_path}")
else:
    print(f"DEBUG: Odds API Key loaded correctly (ending in ...{API_KEY[-4:]})")

REGIONS = "us,uk,eu,au"
MARKETS = "h2h"


def get_mock_odds():
    """Returns a massive pool of simulated odds to power a great search experience even if the API is unreachable."""
    return [
        {"genre": "Soccer", "home_team": "Real Madrid", "away_team": "Manchester City", "bookmakers": [{"title": "Bet365", "markets": [{"key": "h2h", "outcomes": [{"name": "Real Madrid", "price": 2.40}, {"name": "Manchester City", "price": 2.10}]}]}]},
        {"genre": "Soccer", "home_team": "Liverpool", "away_team": "Manchester United", "bookmakers": [{"title": "DraftKings", "markets": [{"key": "h2h", "outcomes": [{"name": "Liverpool", "price": 1.95}, {"name": "Manchester United", "price": 3.40}]}]}]},
        {"genre": "Soccer", "home_team": "Arsenal", "away_team": "Chelsea", "bookmakers": [{"title": "FanDuel", "markets": [{"key": "h2h", "outcomes": [{"name": "Arsenal", "price": 1.85}, {"name": "Chelsea", "price": 4.10}]}]}]},
        {"genre": "Soccer", "home_team": "Bayern Munich", "away_team": "Borussia Dortmund", "bookmakers": [{"title": "Betway", "markets": [{"key": "h2h", "outcomes": [{"name": "Bayern Munich", "price": 1.65}, {"name": "Borussia Dortmund", "price": 4.50}]}]}]},
        {"genre": "Soccer", "home_team": "Barcelona", "away_team": "Paris Saint-Germain", "bookmakers": [{"title": "Pinnacle", "markets": [{"key": "h2h", "outcomes": [{"name": "Barcelona", "price": 2.20}, {"name": "Paris Saint-Germain", "price": 2.30}]}]}]},
        {"genre": "NBA", "home_team": "Los Angeles Lakers", "away_team": "Golden State Warriors", "bookmakers": [{"title": "DraftKings", "markets": [{"key": "h2h", "outcomes": [{"name": "Los Angeles Lakers", "price": 2.10}, {"name": "Golden State Warriors", "price": 1.75}]}]}]},
        {"genre": "NBA", "home_team": "Boston Celtics", "away_team": "Miami Heat", "bookmakers": [{"title": "FanDuel", "markets": [{"key": "h2h", "outcomes": [{"name": "Boston Celtics", "price": 1.45}, {"name": "Miami Heat", "price": 3.20}]}]}]},
        {"genre": "NBA", "home_team": "Dallas Mavericks", "away_team": "Phoenix Suns", "bookmakers": [{"title": "BetMGM", "markets": [{"key": "h2h", "outcomes": [{"name": "Dallas Mavericks", "price": 1.90}, {"name": "Phoenix Suns", "price": 1.90}]}]}]},
        {"genre": "NFL", "home_team": "Kansas City Chiefs", "away_team": "Buffalo Bills", "bookmakers": [{"title": "DraftKings", "markets": [{"key": "h2h", "outcomes": [{"name": "Kansas City Chiefs", "price": 1.80}, {"name": "Buffalo Bills", "price": 2.10}]}]}]},
        {"genre": "NFL", "home_team": "San Francisco 49ers", "away_team": "Philadelphia Eagles", "bookmakers": [{"title": "FanDuel", "markets": [{"key": "h2h", "outcomes": [{"name": "San Francisco 49ers", "price": 1.70}, {"name": "Philadelphia Eagles", "price": 2.20}]}]}]},
        {"genre": "Cricket", "home_team": "India", "away_team": "Pakistan", "bookmakers": [{"title": "Bet365", "markets": [{"key": "h2h", "outcomes": [{"name": "India", "price": 1.65}, {"name": "Pakistan", "price": 2.35}]}]}]},
        {"genre": "Cricket", "home_team": "Australia", "away_team": "England", "bookmakers": [{"title": "William Hill", "markets": [{"key": "h2h", "outcomes": [{"name": "Australia", "price": 1.85}, {"name": "England", "price": 2.05}]}]}]},
        {"genre": "F1", "home_team": "Max Verstappen", "away_team": "Lewis Hamilton", "bookmakers": [{"title": "Pinnacle", "markets": [{"key": "h2h", "outcomes": [{"name": "Max Verstappen", "price": 1.30}, {"name": "Lewis Hamilton", "price": 7.00}]}]}]},
        {"genre": "MMA", "home_team": "Israel Adesanya", "away_team": "Alex Pereira", "bookmakers": [{"title": "DraftKings", "markets": [{"key": "h2h", "outcomes": [{"name": "Israel Adesanya", "price": 1.75}, {"name": "Alex Pereira", "price": 2.15}]}]}]},
        {"genre": "Tennis", "home_team": "Carlos Alcaraz", "away_team": "Jannik Sinner", "bookmakers": [{"title": "Bet365", "markets": [{"key": "h2h", "outcomes": [{"name": "Carlos Alcaraz", "price": 1.80}, {"name": "Jannik Sinner", "price": 2.00}]}]}]},
        {"genre": "AFL", "home_team": "Collingwood Magpies", "away_team": "Brisbane Lions", "bookmakers": [{"title": "Sportsbet", "markets": [{"key": "h2h", "outcomes": [{"name": "Collingwood Magpies", "price": 1.85}, {"name": "Brisbane Lions", "price": 1.95}]}]}]},
        {"genre": "AFL", "home_team": "Carlton Blues", "away_team": "Sydney Swans", "bookmakers": [{"title": "Betfair", "markets": [{"key": "h2h", "outcomes": [{"name": "Carlton Blues", "price": 2.10}, {"name": "Sydney Swans", "price": 1.75}]}]}]},
        {"genre": "NHL", "home_team": "Tampa Bay Lightning", "away_team": "Florida Panthers", "bookmakers": [{"title": "DraftKings", "markets": [{"key": "h2h", "outcomes": [{"name": "Tampa Bay Lightning", "price": 2.05}, {"name": "Florida Panthers", "price": 1.80}]}]}]},
        # Add a few more to make it feel massive
        {"genre": "Soccer", "home_team": "Juventus", "away_team": "Inter Milan", "bookmakers": [{"title": "Bet365", "markets": [{"key": "h2h", "outcomes": [{"name": "Juventus", "price": 2.60}, {"name": "Inter Milan", "price": 2.80}]}]}]},
        {"genre": "NBA", "home_team": "Milwaukee Bucks", "away_team": "Philadelphia 76ers", "bookmakers": [{"title": "FanDuel", "markets": [{"key": "h2h", "outcomes": [{"name": "Milwaukee Bucks", "price": 1.60}, {"name": "Philadelphia 76ers", "price": 2.40}]}]}]},
        {"genre": "MLB", "home_team": "New York Yankees", "away_team": "Boston Red Sox", "bookmakers": [{"title": "DraftKings", "markets": [{"key": "h2h", "outcomes": [{"name": "New York Yankees", "price": 1.85}, {"name": "Boston Red Sox", "price": 1.95}]}]}]}
    ]

# Mapping user-requested sports to The Odds API keys
SPORT_MAPPINGS = {
    "soccer": ["soccer_epl", "soccer_uefa_champs_league", "soccer_spain_la_liga", "soccer_italy_serie_a", "soccer_germany_bundesliga", "soccer_france_ligue_one"],
    "basketball": ["basketball_nba", "basketball_euroleague"],
    "baseball": ["baseball_mlb"],
    "nfl": ["americanfootball_nfl"],
    "nba": ["basketball_nba"],
    "afl": ["aussierules_afl"],
    "f1": ["racing_formula1"],
    "mma": ["mma_mixed_martial_arts"],
    "hockey": ["icehockey_nhl"],
    "handball": ["handball_germany_bundesliga", "handball_france_starligue"],
    "rugby": ["rugbyleague_nrl", "rugbyunion_premiership_rugby"],
    "volleyball": ["volleyball_italy_superlega", "volleyball_france_marmara_spike_league"],
    "cricket": ["cricket_ipl", "cricket_test_match"]
}

# Core Sports Keys for Indexing
CORE_SPORTS = ["upcoming"] + [key for sublist in SPORT_MAPPINGS.values() for key in sublist]

def get_mock_odds():
    """Returns a large pool of realistic matches so the search engine is always warm."""
    return [
        {"genre": "Soccer", "home_team": "Real Madrid", "away_team": "Manchester City", "sport_title": "Soccer", "bookmakers": [{"title": "Bet365", "markets": [{"key": "h2h", "outcomes": [{"name": "Real Madrid", "price": 2.40}, {"name": "Manchester City", "price": 2.10}, {"name": "Draw", "price": 3.20}]}]}, {"title": "Pinnacle", "markets": [{"key": "h2h", "outcomes": [{"name": "Real Madrid", "price": 2.45}, {"name": "Manchester City", "price": 2.05}, {"name": "Draw", "price": 3.25}]}]}]},
        {"genre": "Soccer", "home_team": "Liverpool", "away_team": "Manchester United", "sport_title": "Soccer", "bookmakers": [{"title": "DraftKings", "markets": [{"key": "h2h", "outcomes": [{"name": "Liverpool", "price": 1.95}, {"name": "Manchester United", "price": 3.40}, {"name": "Draw", "price": 3.60}]}]}, {"title": "FanDuel", "markets": [{"key": "h2h", "outcomes": [{"name": "Liverpool", "price": 1.90}, {"name": "Manchester United", "price": 3.50}, {"name": "Draw", "price": 3.70}]}]}]},
        {"genre": "Soccer", "home_team": "Arsenal", "away_team": "Chelsea", "sport_title": "Soccer", "bookmakers": [{"title": "FanDuel", "markets": [{"key": "h2h", "outcomes": [{"name": "Arsenal", "price": 1.85}, {"name": "Chelsea", "price": 4.10}, {"name": "Draw", "price": 3.40}]}]}, {"title": "Betway", "markets": [{"key": "h2h", "outcomes": [{"name": "Arsenal", "price": 1.80}, {"name": "Chelsea", "price": 4.20}, {"name": "Draw", "price": 3.45}]}]}]},
        {"genre": "Soccer", "home_team": "Bayern Munich", "away_team": "Borussia Dortmund", "sport_title": "Soccer", "bookmakers": [{"title": "Betway", "markets": [{"key": "h2h", "outcomes": [{"name": "Bayern Munich", "price": 1.65}, {"name": "Borussia Dortmund", "price": 4.50}]}]}, {"title": "Bet365", "markets": [{"key": "h2h", "outcomes": [{"name": "Bayern Munich", "price": 1.60}, {"name": "Borussia Dortmund", "price": 4.75}]}]}]},
        {"genre": "Soccer", "home_team": "Barcelona", "away_team": "Paris Saint-Germain", "sport_title": "Soccer", "bookmakers": [{"title": "Pinnacle", "markets": [{"key": "h2h", "outcomes": [{"name": "Barcelona", "price": 2.20}, {"name": "Paris Saint-Germain", "price": 2.30}]}]}, {"title": "Unibet", "markets": [{"key": "h2h", "outcomes": [{"name": "Barcelona", "price": 2.15}, {"name": "Paris Saint-Germain", "price": 2.35}]}]}]},
        {"genre": "Soccer", "home_team": "Juventus", "away_team": "Inter Milan", "sport_title": "Soccer", "bookmakers": [{"title": "Bet365", "markets": [{"key": "h2h", "outcomes": [{"name": "Juventus", "price": 2.60}, {"name": "Inter Milan", "price": 2.80}, {"name": "Draw", "price": 3.10}]}]}]},
        {"genre": "NBA", "home_team": "Los Angeles Lakers", "away_team": "Golden State Warriors", "sport_title": "Basketball", "bookmakers": [{"title": "DraftKings", "markets": [{"key": "h2h", "outcomes": [{"name": "Los Angeles Lakers", "price": 2.10}, {"name": "Golden State Warriors", "price": 1.75}]}]}, {"title": "FanDuel", "markets": [{"key": "h2h", "outcomes": [{"name": "Los Angeles Lakers", "price": 2.15}, {"name": "Golden State Warriors", "price": 1.70}]}]}]},
        {"genre": "NBA", "home_team": "Boston Celtics", "away_team": "Miami Heat", "sport_title": "Basketball", "bookmakers": [{"title": "FanDuel", "markets": [{"key": "h2h", "outcomes": [{"name": "Boston Celtics", "price": 1.45}, {"name": "Miami Heat", "price": 3.20}]}]}, {"title": "BetMGM", "markets": [{"key": "h2h", "outcomes": [{"name": "Boston Celtics", "price": 1.48}, {"name": "Miami Heat", "price": 3.10}]}]}]},
        {"genre": "NBA", "home_team": "Dallas Mavericks", "away_team": "Phoenix Suns", "sport_title": "Basketball", "bookmakers": [{"title": "BetMGM", "markets": [{"key": "h2h", "outcomes": [{"name": "Dallas Mavericks", "price": 1.90}, {"name": "Phoenix Suns", "price": 1.90}]}]}, {"title": "Caesars", "markets": [{"key": "h2h", "outcomes": [{"name": "Dallas Mavericks", "price": 1.88}, {"name": "Phoenix Suns", "price": 1.92}]}]}]},
        {"genre": "NBA", "home_team": "Milwaukee Bucks", "away_team": "Philadelphia 76ers", "sport_title": "Basketball", "bookmakers": [{"title": "FanDuel", "markets": [{"key": "h2h", "outcomes": [{"name": "Milwaukee Bucks", "price": 1.60}, {"name": "Philadelphia 76ers", "price": 2.40}]}]}]},
        {"genre": "NFL", "home_team": "Kansas City Chiefs", "away_team": "Buffalo Bills", "sport_title": "American Football", "bookmakers": [{"title": "DraftKings", "markets": [{"key": "h2h", "outcomes": [{"name": "Kansas City Chiefs", "price": 1.80}, {"name": "Buffalo Bills", "price": 2.10}]}]}, {"title": "FanDuel", "markets": [{"key": "h2h", "outcomes": [{"name": "Kansas City Chiefs", "price": 1.78}, {"name": "Buffalo Bills", "price": 2.12}]}]}]},
        {"genre": "NFL", "home_team": "San Francisco 49ers", "away_team": "Philadelphia Eagles", "sport_title": "American Football", "bookmakers": [{"title": "FanDuel", "markets": [{"key": "h2h", "outcomes": [{"name": "San Francisco 49ers", "price": 1.70}, {"name": "Philadelphia Eagles", "price": 2.20}]}]}, {"title": "BetMGM", "markets": [{"key": "h2h", "outcomes": [{"name": "San Francisco 49ers", "price": 1.68}, {"name": "Philadelphia Eagles", "price": 2.25}]}]}]},
        {"genre": "Cricket", "home_team": "India", "away_team": "Pakistan", "sport_title": "Cricket", "bookmakers": [{"title": "Bet365", "markets": [{"key": "h2h", "outcomes": [{"name": "India", "price": 1.65}, {"name": "Pakistan", "price": 2.35}]}]}, {"title": "Betway", "markets": [{"key": "h2h", "outcomes": [{"name": "India", "price": 1.60}, {"name": "Pakistan", "price": 2.40}]}]}]},
        {"genre": "Cricket", "home_team": "Australia", "away_team": "England", "sport_title": "Cricket", "bookmakers": [{"title": "William Hill", "markets": [{"key": "h2h", "outcomes": [{"name": "Australia", "price": 1.85}, {"name": "England", "price": 2.05}]}]}, {"title": "Pinnacle", "markets": [{"key": "h2h", "outcomes": [{"name": "Australia", "price": 1.82}, {"name": "England", "price": 2.08}]}]}]},
        {"genre": "F1", "home_team": "Max Verstappen", "away_team": "Lewis Hamilton", "sport_title": "Formula 1", "bookmakers": [{"title": "Pinnacle", "markets": [{"key": "h2h", "outcomes": [{"name": "Max Verstappen", "price": 1.30}, {"name": "Lewis Hamilton", "price": 7.00}]}]}, {"title": "Bet365", "markets": [{"key": "h2h", "outcomes": [{"name": "Max Verstappen", "price": 1.28}, {"name": "Lewis Hamilton", "price": 7.50}]}]}]},
        {"genre": "MMA", "home_team": "Israel Adesanya", "away_team": "Alex Pereira", "sport_title": "MMA", "bookmakers": [{"title": "DraftKings", "markets": [{"key": "h2h", "outcomes": [{"name": "Israel Adesanya", "price": 1.75}, {"name": "Alex Pereira", "price": 2.15}]}]}, {"title": "BetOnline.ag", "markets": [{"key": "h2h", "outcomes": [{"name": "Israel Adesanya", "price": 1.80}, {"name": "Alex Pereira", "price": 2.10}]}]}]},
        {"genre": "Tennis", "home_team": "Carlos Alcaraz", "away_team": "Jannik Sinner", "sport_title": "Tennis", "bookmakers": [{"title": "Bet365", "markets": [{"key": "h2h", "outcomes": [{"name": "Carlos Alcaraz", "price": 1.80}, {"name": "Jannik Sinner", "price": 2.00}]}]}, {"title": "Pinnacle", "markets": [{"key": "h2h", "outcomes": [{"name": "Carlos Alcaraz", "price": 1.82}, {"name": "Jannik Sinner", "price": 1.98}]}]}]},
        {"genre": "Tennis", "home_team": "Novak Djokovic", "away_team": "Rafael Nadal", "sport_title": "Tennis", "bookmakers": [{"title": "Bet365", "markets": [{"key": "h2h", "outcomes": [{"name": "Novak Djokovic", "price": 2.15}, {"name": "Rafael Nadal", "price": 1.70}]}]}, {"title": "Pinnacle", "markets": [{"key": "h2h", "outcomes": [{"name": "Novak Djokovic", "price": 1.75}, {"name": "Rafael Nadal", "price": 2.10}]}]}]},
        {"genre": "AFL", "home_team": "Collingwood Magpies", "away_team": "Brisbane Lions", "sport_title": "AFL", "bookmakers": [{"title": "Betway", "markets": [{"key": "h2h", "outcomes": [{"name": "Collingwood Magpies", "price": 1.85}, {"name": "Brisbane Lions", "price": 1.95}]}]}]},
        {"genre": "NHL", "home_team": "Tampa Bay Lightning", "away_team": "Florida Panthers", "sport_title": "Ice Hockey", "bookmakers": [{"title": "DraftKings", "markets": [{"key": "h2h", "outcomes": [{"name": "Tampa Bay Lightning", "price": 2.05}, {"name": "Florida Panthers", "price": 1.80}]}]}, {"title": "FanDuel", "markets": [{"key": "h2h", "outcomes": [{"name": "Tampa Bay Lightning", "price": 2.08}, {"name": "Florida Panthers", "price": 1.78}]}]}]},
        {"genre": "MLB", "home_team": "New York Yankees", "away_team": "Boston Red Sox", "sport_title": "Baseball", "bookmakers": [{"title": "DraftKings", "markets": [{"key": "h2h", "outcomes": [{"name": "New York Yankees", "price": 1.85}, {"name": "Boston Red Sox", "price": 1.95}]}]}, {"title": "Caesars", "markets": [{"key": "h2h", "outcomes": [{"name": "New York Yankees", "price": 1.83}, {"name": "Boston Red Sox", "price": 1.97}]}]}]},
    ]

def get_session():
    session = requests.Session()
    retry = Retry(connect=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    # Add a real-looking User-Agent to avoid being blocked/reset
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })
    return session

def get_live_odds(sport_key="upcoming"):
    """Fetches real-time odds from The Odds API for a specific sport."""
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/"
    params = {
        "apiKey": API_KEY,
        "regions": REGIONS,
        "markets": MARKETS,
        "oddsFormat": "decimal"
    }
    
    session = get_session()
    
    for attempt in range(2): 
        try:
            response = session.get(url, params=params, timeout=10)
            if response.status_code != 200:
                print(f"API Debug ({sport_key}) {response.status_code}: {response.text}")
            if response.status_code == 422: return [] 
            response.raise_for_status()
            data = response.json()
            for match in data:
                match['genre'] = match.get('sport_title', 'Unknown')
            return data
        except Exception as e:
            print(f"Error fetching {sport_key}: {e}")
            time.sleep(2) # Longer wait on error
            
    return []

def get_all_active_odds():
    """Builds a massive pool of odds across multiple sports for search indexing."""
    pool = []
    
    # We fetch each sport in the core list with a delay to avoid ConnectionResetError
    for sport in CORE_SPORTS:
        try:
            odds = get_live_odds(sport)
            if odds:
                pool.extend(odds)
            # Mandatory sleep to prevent being throttled/reset by The Odds API
            time.sleep(1.5) 
        except Exception as e:
            print(f"Error indexing {sport}: {e}")
            continue
            
    # Remove duplicates if any (based on id)
    seen = set()
    unique_pool = []
    for match in pool:
        mid = match.get('id')
        if mid not in seen:
            unique_pool.append(match)
            seen.add(mid)
            
    return unique_pool


def get_best_odds(api_data):
    """
    Cleans real API data and finds the best odds across all bookmakers.
    """
    best_odds_list = []
    
    # api_data is a list of matches
    for match in api_data:
        match_name = f"{match.get('home_team', 'Unknown')} vs {match.get('away_team', 'Unknown')}"
        genre = match.get('genre', 'Unknown')
        
        # We use a dictionary temporarily to track the best price for each outcome
        best_prices_dict = {}
        
        bookmakers = match.get('bookmakers', [])
        for bookie in bookmakers:
            markets = bookie.get('markets', [])
            for market in markets:
                if market['key'] == 'h2h':
                    for outcome in market['outcomes']:
                        name = outcome['name']
                        price = outcome['price']
                        
                        # If this price is better than what we have, save it
                        if name not in best_prices_dict or price > best_prices_dict[name]['odds']:
                            best_prices_dict[name] = {
                                "outcome": name,
                                "odds": price,
                                "book": bookie['title']
                            }
        
        # HERE IS THE FIX: Convert the dictionary values back to a list
        final_best_odds = list(best_prices_dict.values())
        
        if final_best_odds:
            best_odds_list.append({
                "match": match_name,
                "genre": genre,
                "best_odds": final_best_odds
            })
            
    return best_odds_list