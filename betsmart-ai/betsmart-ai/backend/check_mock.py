from services.odds_fetcher import get_mock_odds, get_best_odds
data = get_mock_odds()
best = get_best_odds(data)
print(f"Mock matches: {len(data)}, Best odds entries: {len(best)}")
for b in best[:6]:
    books = [o["book"] + "@" + str(o["odds"]) for o in b["best_odds"][:2]]
    print(f"  - {b['match']} ({b.get('genre','?')}): {books}")
