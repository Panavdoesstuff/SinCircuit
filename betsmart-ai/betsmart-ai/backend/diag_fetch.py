import sys
import os

# Add the current directory to sys.path so we can import odds_fetcher
sys.path.append(os.getcwd())

import services.odds_fetcher

def test_fetch():
    print("Testing get_all_active_odds...")
    data = odds_fetcher.get_all_active_odds()
    print(f"Total matches fetched: {len(data)}")
    
    if len(data) == 0:
        print("Detailed test of one sport (soccer_epl):")
        res = odds_fetcher.get_live_odds("soccer_epl")
        print(f"Soccer EPL matches: {len(res)}")
        if len(res) == 0:
             # Try upcoming
             print("Trying upcoming:")
             res2 = odds_fetcher.get_live_odds("upcoming")
             print(f"Upcoming: {len(res2)}")

if __name__ == "__main__":
    test_fetch()
