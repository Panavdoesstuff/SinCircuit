def find_arbitrage(best_odds_list):
    opportunities = []
    for match in best_odds_list:
        # Safety: Filter out any 0 or None odds
        odds_values = [o['odds'] for o in match['best_odds'] if o.get('odds', 0) > 0]
        
        # Only calculate if we have at least 2 valid outcomes
        if len(odds_values) >= 2:
            try:
                margin = sum(1/o for o in odds_values)
                if margin < 1.0:
                    profit = (1 - margin) * 100
                    opportunities.append({
                        "match": match['match'],
                        "arb_margin": round(profit, 2),
                        "best_odds": match['best_odds']
                    })
            except ZeroDivisionError:
                continue 
    return opportunities

def get_bookmaker_link(book_name: str) -> dict:
    """Returns the official homepage and regional metadata for a given bookmaker."""
    links = {
        "Bet365": {"url": "https://www.bet365.com/", "region_locked": False},
        "Pinnacle": {"url": "https://www.pinnacle.com/", "region_locked": False},
        "DraftKings": {"url": "https://sportsbook.draftkings.com/", "region_locked": True},
        "FanDuel": {"url": "https://sportsbook.fanduel.com/", "region_locked": True},
        "Betway": {"url": "https://betway.com/", "region_locked": False},
        "Caesars": {"url": "https://www.caesars.com/sportsbook-and-casino", "region_locked": True},
        "BetMGM": {"url": "https://sports.betmgm.com/", "region_locked": True},
        "Bovada": {"url": "https://www.bovada.lv/", "region_locked": False},
        "William Hill": {"url": "https://sports.williamhill.com/", "region_locked": False},
        "TwinSpires": {"url": "https://www.twinspires.com/", "region_locked": True},
        "TVG": {"url": "https://www.tvg.com/", "region_locked": True},
        "Betfair": {"url": "https://www.betfair.com/", "region_locked": False},
        "Unibet": {"url": "https://www.unibet.com/", "region_locked": False},
        "888sport": {"url": "https://www.888sport.com/", "region_locked": False},
        "Stake": {"url": "https://stake.com/", "region_locked": False},
        "Ladbrokes": {"url": "https://www.ladbrokes.com/", "region_locked": False},
        "Coral": {"url": "https://www.coral.co.uk/", "region_locked": False},
        "Paddy Power": {"url": "https://www.paddypower.com/", "region_locked": False},
        "Sky Bet": {"url": "https://www.skybet.com/", "region_locked": False},
        "BetRivers": {"url": "https://www.betrivers.com/", "region_locked": True},
        "Barstool Sportsbook": {"url": "https://www.barstoolsportsbook.com/", "region_locked": True},
        "PointsBet": {"url": "https://www.pointsbet.com/", "region_locked": True},
        "LowVig.ag": {"url": "https://www.lowvig.ag/", "region_locked": False},
        "BetOnline.ag": {"url": "https://www.betonline.ag/", "region_locked": False},
        "MyBookie.ag": {"url": "https://www.mybookie.ag/", "region_locked": False},
        "BetUS": {"url": "https://www.betus.com.pa/", "region_locked": False},
        "Marathonbet": {"url": "https://www.marathonbet.com/", "region_locked": False},
        "1xBet": {"url": "https://1xbet.com/", "region_locked": False},
    }
    
    # Return matched info or a Google Search fallback if not in dictionary
    if book_name in links:
        return links[book_name]
    
    # Generic fallback: search for the bookmaker
    clean_name = book_name.replace(" ", "+")
    return {
        "url": f"https://www.google.com/search?q={clean_name}+official+site",
        "region_locked": False # Unknown, assume false for fallback
    }

def stake_distribution(best_odds, total_stake=1000):
    valid_odds = [o for o in best_odds if o.get('odds', 0) > 0]
    if not valid_odds: return []
    
    try:
        margin = sum(1/o['odds'] for o in valid_odds)
        bets = []
        for o in valid_odds:
            individual_stake = (1/o['odds']) / margin * total_stake
            book_info = get_bookmaker_link(o['book'])
            bets.append({
                "outcome": o['outcome'],
                "stake": round(individual_stake, 2),
                "book": o['book'],
                "odds": o['odds'],
                "link": book_info["url"],
                "region_locked": book_info["region_locked"]
            })
        return bets
    except ZeroDivisionError:
        return []