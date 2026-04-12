from services.odds_fetcher import get_mock_odds, get_best_odds

data = get_mock_odds()
best = get_best_odds(data)

print(best)